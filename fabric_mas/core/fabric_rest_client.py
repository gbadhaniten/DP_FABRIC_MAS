"""
fabric_rest_client.py — Microsoft Fabric REST API Client
==========================================================
Fully dynamic authentication — no credentials stored anywhere.

The client uses Azure Identity to acquire tokens from the user's session:
    1. Tries cached tokens / VS Code / Azure CLI (whatever is available)
    2. Decodes the JWT to check which account was used
    3. If the account is NOT an _AZR account (which has Fabric access),
       automatically opens a browser login prompt
    4. Caches the session token — subsequent calls reuse it

Two types of accounts in the organisation:
    @ten.com          — corporate account (GitHub, general services)
    _AZR@domain.com   — Azure resource account (Fabric, Azure resources)

The client ensures Fabric REST calls always use the _AZR account.

Fabric REST API base: https://api.fabric.microsoft.com/v1

Reference: https://learn.microsoft.com/en-us/rest/api/fabric/core/items
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# Fabric API constants
FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"


@dataclass
class RestResult:
    """Result of a Fabric REST API call."""
    success: bool
    status_code: int
    data: Any
    error: str
    elapsed_seconds: float


# Marker used to identify Azure accounts that have Fabric resource access.
# Accounts whose UPN (email) contains this substring are treated as
# "resource accounts".  This is detected dynamically from the JWT token
# — no credentials are stored anywhere.
_AZR_ACCOUNT_MARKER = "_azr"


class FabricRestClient:
    """
    REST client for Microsoft Fabric using Azure Identity.

    Authentication is fully dynamic — no credentials are stored:

    1. Acquires a token using the Azure credential chain
       (token cache → VS Code → Azure CLI → interactive browser)
    2. Inspects the JWT to check which account was used
    3. If the account is NOT an _AZR account (no Fabric access),
       automatically opens a browser login prompt so the user can
       sign in with their _AZR account
    4. Caches the session — subsequent calls reuse the token until
       it expires

    This mirrors how MS Fabric MCP handles auth:
    - Use the signed-in session if it has the right permissions
    - Open a login prompt if not
    """

    def __init__(
        self,
        default_workspace_id: Optional[str] = None,
        dry_run: bool = False,
        timeout: int = 60,
    ):
        self.default_workspace_id = default_workspace_id
        self.dry_run = dry_run
        self.timeout = timeout
        self._token: Optional[str] = None
        self._token_expires: float = 0
        self._credential = None
        self._interactive_credential = None  # fallback for re-auth
        self._authenticated_upn: Optional[str] = None
        self._workspace_name_cache: Dict[str, str] = {}  # name -> id

    # ------------------------------------------------------------------
    # JWT helpers (decode token to read identity — no secrets involved)
    # ------------------------------------------------------------------
    @staticmethod
    def _decode_jwt_claims(token: str) -> Dict[str, Any]:
        """Decode the payload of a JWT token (no signature verification needed)."""
        import base64
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        try:
            return json.loads(base64.urlsafe_b64decode(padded))
        except Exception:
            return {}

    @staticmethod
    def _is_azr_account(upn: str) -> bool:
        """Check whether a UPN belongs to an _AZR (resource) account."""
        return _AZR_ACCOUNT_MARKER in upn.lower() if upn else False

    # ------------------------------------------------------------------
    # Authentication — fully dynamic, no stored credentials
    # ------------------------------------------------------------------
    def _build_default_chain(self):
        """
        Build the default credential chain.

        Order:
        1. EnvironmentCredential          — CI / service principals
        2. SharedTokenCacheCredential      — picks up any cached Azure login
        3. VisualStudioCodeCredential      — VS Code Azure Resources sign-in
        4. AzureCliCredential              — az login session
        5. InteractiveBrowserCredential    — opens browser (last resort)
        """
        from azure.identity import (
            ChainedTokenCredential,
            EnvironmentCredential,
            SharedTokenCacheCredential,
            AzureCliCredential,
            InteractiveBrowserCredential,
        )

        creds = [
            EnvironmentCredential(),
            SharedTokenCacheCredential(),
        ]
        try:
            from azure.identity import VisualStudioCodeCredential
            creds.append(VisualStudioCodeCredential())
        except Exception:
            pass
        creds.append(AzureCliCredential())
        creds.append(InteractiveBrowserCredential())
        return ChainedTokenCredential(*creds)

    def _build_interactive_credential(self, login_hint: Optional[str] = None):
        """Build an interactive browser credential with optional login hint."""
        from azure.identity import InteractiveBrowserCredential
        kwargs = {}
        if login_hint:
            kwargs["login_hint"] = login_hint
        return InteractiveBrowserCredential(**kwargs)

    def _get_credential(self):
        """Lazy-init the credential (first call only)."""
        if self._credential is None:
            try:
                self._credential = self._build_default_chain()
            except ImportError:
                raise ImportError(
                    "azure-identity not installed. "
                    "Run: pip install azure-identity azure-identity-broker"
                )
            logger.info("Azure credential chain initialised (dynamic, session-based)")
        return self._credential

    def _get_token(self) -> str:
        """
        Get a valid access token, with automatic _AZR account validation.

        Flow:
        1. Try the default credential chain (cache / VS Code / CLI / browser)
        2. Decode the JWT and check which account was used
        3. If NOT an _AZR account → open a fresh browser login prompt
           so the user can sign in with their _AZR account
        4. Cache the token for subsequent calls
        """
        now = time.time()
        if self._token and now < self._token_expires - 60:
            return self._token

        credential = self._get_credential()
        token_obj = credential.get_token(FABRIC_SCOPE)
        claims = self._decode_jwt_claims(token_obj.token)
        upn = claims.get("upn", claims.get("preferred_username", ""))

        if not self._is_azr_account(upn):
            # The session account doesn't have Fabric access — re-auth
            logger.warning(
                "Session account '%s' is not an _AZR account. "
                "Opening browser login for Azure resource access...",
                upn,
            )
            # Build a fresh interactive credential.
            # If we already know an _AZR UPN from a previous session we
            # use it as a login_hint; otherwise the user picks the account.
            hint = self._authenticated_upn if self._authenticated_upn else None
            self._interactive_credential = self._build_interactive_credential(
                login_hint=hint
            )
            token_obj = self._interactive_credential.get_token(FABRIC_SCOPE)
            claims = self._decode_jwt_claims(token_obj.token)
            upn = claims.get("upn", claims.get("preferred_username", ""))

            if not self._is_azr_account(upn):
                logger.error(
                    "Authenticated as '%s' which is still not an _AZR account. "
                    "Please sign in with your _AZR account that has Fabric access.",
                    upn,
                )
                raise PermissionError(
                    f"Fabric requires an _AZR account. "
                    f"You signed in as '{upn}'. "
                    f"Please sign in with your _AZR account "
                    f"(e.g. yourname_azr@domain.com) and try again."
                )

            # Future calls should go through this credential directly
            self._credential = self._interactive_credential

        self._token = token_obj.token
        self._token_expires = token_obj.expires_on
        self._authenticated_upn = upn
        logger.info("Fabric token acquired for %s", upn)
        return self._token

    def _headers(self) -> Dict[str, str]:
        """Build request headers with auth token."""
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

    def get_authenticated_account(self) -> Optional[str]:
        """Return the UPN of the currently authenticated account, or None."""
        return self._authenticated_upn

    def check_auth(self) -> Tuple[bool, str]:
        """
        Test authentication and return (success, account_upn).

        If the current session is not an _AZR account, this will
        automatically open a browser login prompt.
        """
        try:
            self._get_token()
            return True, self._authenticated_upn or "unknown"
        except Exception as exc:
            logger.error("Auth check failed: %s", exc)
            return False, str(exc)

    # ------------------------------------------------------------------
    # Workspace resolution (name → ID)
    # ------------------------------------------------------------------
    def resolve_workspace_id(self, workspace: str) -> Optional[str]:
        """
        Resolve a workspace name or ID to a workspace ID.
        If it looks like a GUID, return it directly.
        Otherwise, search by name.
        """
        if not workspace:
            return self.default_workspace_id

        # Already a GUID?
        import re
        if re.match(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
            workspace,
        ):
            return workspace

        # Check cache
        wl = workspace.lower()
        if wl in self._workspace_name_cache:
            return self._workspace_name_cache[wl]

        # List workspaces and find by name
        result = self.list_workspaces()
        if result.success:
            # _paginated_get returns a flat list; handle dict wrapper too
            items = result.data
            if isinstance(items, dict):
                items = items.get("value", [])
            if isinstance(items, list):
                for ws in items:
                    name = ws.get("displayName", "")
                    ws_id = ws.get("id", "")
                    self._workspace_name_cache[name.lower()] = ws_id
                    if name.lower() == wl:
                        return ws_id

        logger.warning("Workspace '%s' not found", workspace)
        return None

    # ------------------------------------------------------------------
    # Core HTTP methods
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        url: str,
        body: Optional[Dict] = None,
        description: str = "",
    ) -> RestResult:
        """Make an authenticated request to the Fabric API."""
        if self.dry_run:
            logger.info("[DRY-RUN] %s %s body=%s", method, url, body)
            return RestResult(
                success=True,
                status_code=200,
                data={"dry_run": True, "method": method, "url": url, "body": body},
                error="",
                elapsed_seconds=0,
            )

        start = time.monotonic()
        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=self._headers(),
                json=body,
                timeout=self.timeout,
            )
            elapsed = round(time.monotonic() - start, 2)

            # Parse response
            data = None
            if resp.text:
                try:
                    data = resp.json()
                except Exception:
                    data = resp.text

            success = 200 <= resp.status_code < 300
            error = ""
            if not success:
                error = self._extract_error(data, resp.status_code)
                logger.warning(
                    "API %s %s → %d: %s (%ss)",
                    method, url, resp.status_code, error, elapsed,
                )
            else:
                logger.info(
                    "API %s %s → %d (%ss) %s",
                    method, url, resp.status_code, elapsed, description,
                )

            return RestResult(
                success=success,
                status_code=resp.status_code,
                data=data,
                error=error,
                elapsed_seconds=elapsed,
            )

        except requests.exceptions.Timeout:
            elapsed = round(time.monotonic() - start, 2)
            return RestResult(False, 0, None, f"Timeout after {self.timeout}s", elapsed)
        except Exception as exc:
            elapsed = round(time.monotonic() - start, 2)
            return RestResult(False, 0, None, str(exc), elapsed)

    def _extract_error(self, data: Any, status_code: int) -> str:
        """Extract a human-readable error message from API response."""
        if isinstance(data, dict):
            err = data.get("error", {})
            if isinstance(err, dict):
                code = err.get("code", "")
                msg = err.get("message", "")
                return f"{code}: {msg}" if code else msg
            return str(err) or f"HTTP {status_code}"
        return str(data) if data else f"HTTP {status_code}"

    # ------------------------------------------------------------------
    # Workspace operations
    # ------------------------------------------------------------------
    def _paginated_get(self, url: str, description: str = "") -> RestResult:
        """
        Fetch all pages of a paginated Fabric API response.

        The Fabric REST API returns ``{"value": [...], "continuationUri": "..."}``.
        This helper follows ``continuationUri`` until all pages are collected.
        """
        all_items: List[Dict[str, Any]] = []
        next_url: Optional[str] = url

        while next_url:
            result = self._request("GET", next_url, description=description)
            if not result.success:
                return result  # propagate error from any page

            data = result.data
            if isinstance(data, dict):
                page_items = data.get("value", [])
                all_items.extend(page_items)
                next_url = data.get("continuationUri") or data.get("@odata.nextLink")
            else:
                # Unexpected shape — return as-is
                return result

        return RestResult(
            success=True,
            status_code=200,
            data=all_items,  # flat list of all items across pages
            error="",
            elapsed_seconds=0,
        )

    def list_workspaces(self) -> RestResult:
        """List **all** accessible workspaces (handles pagination)."""
        return self._paginated_get(f"{FABRIC_API_BASE}/workspaces", description="list workspaces")

    def get_workspace(self, workspace_id: str) -> RestResult:
        """Get workspace details."""
        return self._request(
            "GET",
            f"{FABRIC_API_BASE}/workspaces/{workspace_id}",
            description=f"get workspace {workspace_id}",
        )

    # ------------------------------------------------------------------
    # Generic item CRUD (works for Lakehouse, Notebook, Warehouse, etc.)
    # ------------------------------------------------------------------
    def create_item(
        self,
        workspace_id: str,
        item_type: str,
        display_name: str,
        description: str = "",
        definition: Optional[Dict] = None,
    ) -> RestResult:
        """
        Create a Fabric item in a workspace.

        Args:
            workspace_id: GUID of the target workspace.
            item_type: Fabric item type (e.g. "Lakehouse", "Notebook", "Warehouse").
            display_name: Display name for the item.
            description: Optional description.
            definition: Optional item definition payload.
        """
        body: Dict[str, Any] = {
            "type": item_type,
            "displayName": display_name,
        }
        if description:
            body["description"] = description
        if definition:
            body["definition"] = definition

        return self._request(
            "POST",
            f"{FABRIC_API_BASE}/workspaces/{workspace_id}/items",
            body=body,
            description=f"create {item_type} '{display_name}'",
        )

    def get_item(self, workspace_id: str, item_id: str) -> RestResult:
        """Get details of a specific item."""
        return self._request(
            "GET",
            f"{FABRIC_API_BASE}/workspaces/{workspace_id}/items/{item_id}",
            description=f"get item {item_id}",
        )

    def list_items(
        self,
        workspace_id: str,
        item_type: Optional[str] = None,
    ) -> RestResult:
        """
        List items in a workspace, optionally filtered by type.

        Args:
            workspace_id: GUID of the workspace.
            item_type: Optional filter (e.g. "Lakehouse", "Notebook").
        """
        url = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/items"
        if item_type:
            url += f"?type={item_type}"
        return self._paginated_get(url, description=f"list items (type={item_type})")

    def update_item(
        self,
        workspace_id: str,
        item_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> RestResult:
        """Update an item's display name and/or description."""
        body: Dict[str, Any] = {}
        if display_name is not None:
            body["displayName"] = display_name
        if description is not None:
            body["description"] = description

        return self._request(
            "PATCH",
            f"{FABRIC_API_BASE}/workspaces/{workspace_id}/items/{item_id}",
            body=body,
            description=f"update item {item_id}",
        )

    def delete_item(self, workspace_id: str, item_id: str) -> RestResult:
        """Delete an item from a workspace."""
        return self._request(
            "DELETE",
            f"{FABRIC_API_BASE}/workspaces/{workspace_id}/items/{item_id}",
            description=f"delete item {item_id}",
        )

    # ------------------------------------------------------------------
    # Convenience: type-specific shortcuts
    # ------------------------------------------------------------------
    def create_lakehouse(
        self, workspace_id: str, display_name: str, description: str = ""
    ) -> RestResult:
        return self.create_item(workspace_id, "Lakehouse", display_name, description)

    def create_warehouse(
        self, workspace_id: str, display_name: str, description: str = ""
    ) -> RestResult:
        return self.create_item(workspace_id, "Warehouse", display_name, description)

    def create_notebook(
        self, workspace_id: str, display_name: str, description: str = ""
    ) -> RestResult:
        return self.create_item(workspace_id, "Notebook", display_name, description)

    def list_lakehouses(self, workspace_id: str) -> RestResult:
        return self.list_items(workspace_id, "Lakehouse")

    def list_warehouses(self, workspace_id: str) -> RestResult:
        return self.list_items(workspace_id, "Warehouse")

    def list_notebooks(self, workspace_id: str) -> RestResult:
        return self.list_items(workspace_id, "Notebook")
