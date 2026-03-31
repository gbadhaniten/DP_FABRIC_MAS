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
from pathlib import Path
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

    Authentication is fully dynamic — no credentials are stored in code:

    1. First run: opens a browser login prompt → user signs in with _AZR account
    2. Token + refresh token are persisted to the OS-level secure cache
       (Windows Credential Manager / macOS Keychain / Linux keyring)
    3. All subsequent calls (including across MCP server restarts) silently
       reuse the cached session — no browser prompt needed
    4. Only re-prompts when the refresh token expires (typically 90 days)
       or the cache is cleared

    The JWT is inspected to verify an _AZR account was used. If the first
    cached/session token belongs to a non-_AZR account, a browser prompt
    opens automatically so the user can sign in with the correct account.

    This mirrors how MS Fabric MCP handles auth.
    """

    # Persistent cache name — stored in OS secure credential store
    _CACHE_NAME = "fabric_mas_token_cache"

    # AuthenticationRecord file — stores *which account* to use silently.
    # This file contains NO secrets — just tenant/client/authority metadata
    # that tells InteractiveBrowserCredential to silently refresh the cached
    # refresh token instead of opening the browser.
    _AUTH_RECORD_DIR = Path.home() / ".fabric_mas"
    _AUTH_RECORD_FILE = _AUTH_RECORD_DIR / "auth_record.json"

    # ------------------------------------------------------------------
    # AuthenticationRecord persistence (login once, reuse forever)
    # ------------------------------------------------------------------
    @classmethod
    def _save_auth_record(cls, record) -> None:
        """Persist AuthenticationRecord to disk (no secrets — just account metadata)."""
        try:
            cls._AUTH_RECORD_DIR.mkdir(parents=True, exist_ok=True)
            cls._AUTH_RECORD_FILE.write_text(record.serialize(), encoding="utf-8")
            logger.info("Auth record saved to %s", cls._AUTH_RECORD_FILE)
        except Exception as exc:
            logger.warning("Could not save auth record: %s", exc)

    @classmethod
    def _load_auth_record(cls):
        """Load a previously saved AuthenticationRecord, or None."""
        try:
            if cls._AUTH_RECORD_FILE.exists():
                from azure.identity import AuthenticationRecord
                data = cls._AUTH_RECORD_FILE.read_text(encoding="utf-8")
                record = AuthenticationRecord.deserialize(data)
                logger.info("Loaded cached auth record from %s", cls._AUTH_RECORD_FILE)
                return record
        except Exception as exc:
            logger.warning("Could not load auth record: %s", exc)
        return None

    @classmethod
    def clear_auth_cache(cls) -> bool:
        """Clear the saved auth record (forces re-login on next call)."""
        try:
            if cls._AUTH_RECORD_FILE.exists():
                cls._AUTH_RECORD_FILE.unlink()
                logger.info("Auth record cleared.")
            return True
        except Exception as exc:
            logger.warning("Could not clear auth record: %s", exc)
            return False

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
    # Persistent token cache — login once, reuse across restarts
    # ------------------------------------------------------------------
    @staticmethod
    def _get_cache_options():
        """
        Build TokenCachePersistenceOptions for the OS secure credential store.

        This stores refresh tokens in:
        - Windows: Windows Credential Manager
        - macOS:   Keychain
        - Linux:   keyring / encrypted file

        No passwords or secrets are stored in code or config files.
        """
        try:
            from azure.identity import TokenCachePersistenceOptions
            return TokenCachePersistenceOptions(
                name=FabricRestClient._CACHE_NAME,
                allow_unencrypted_storage=False,
            )
        except ImportError:
            return None

    def _build_credential_with_cache(self):
        """
        Build the best credential for Fabric auth.

        Strategy:
        - If an AuthenticationRecord exists on disk → build an
          InteractiveBrowserCredential with it → SILENT token refresh
        - If no record exists → build a bare InteractiveBrowserCredential
          → browser opens ONCE → we'll save the record after authenticate()

        Fallback chain (EnvironmentCredential → AzureCLI) only for CI/service
        principal scenarios where no interactive login is possible.
        """
        from azure.identity import InteractiveBrowserCredential

        cache_opts = self._get_cache_options()
        auth_record = self._load_auth_record()

        kwargs = {}
        if cache_opts:
            kwargs["cache_persistence_options"] = cache_opts
        if auth_record:
            kwargs["authentication_record"] = auth_record
            logger.info(
                "Using cached auth record — silent token refresh (no browser)"
            )

        return InteractiveBrowserCredential(**kwargs)

    def _build_interactive_credential(self, login_hint: Optional[str] = None):
        """Build a fresh interactive browser credential (forces browser prompt)."""
        from azure.identity import InteractiveBrowserCredential
        cache_opts = self._get_cache_options()
        kwargs = {}
        if login_hint:
            kwargs["login_hint"] = login_hint
        if cache_opts:
            kwargs["cache_persistence_options"] = cache_opts
        # Don't pass old auth_record here — we WANT the browser to open
        # so user can sign in with the correct _AZR account
        return InteractiveBrowserCredential(**kwargs)

    def _get_credential(self):
        """Lazy-init the credential chain (first call only)."""
        if self._credential is None:
            try:
                self._credential = self._build_credential_with_cache()
            except ImportError:
                raise ImportError(
                    "azure-identity not installed. "
                    "Run: pip install azure-identity azure-identity-broker"
                )
            logger.info("Azure credential chain ready (persistent cache enabled)")
        return self._credential

    def _get_token(self) -> str:
        """
        Get a valid access token with _AZR account validation.

        Flow:
        1. Try cached token (in-memory) — instant, no I/O
        2. If AuthenticationRecord exists → silent refresh (no browser)
        3. If no AuthenticationRecord → call authenticate() → browser opens ONCE
           → save AuthenticationRecord to disk
        4. Decode JWT → verify it's an _AZR account
        5. If wrong account → clear cache → re-auth with browser
        6. Cache token in-memory for rest of session

        First run:  browser opens → save AuthenticationRecord → done
        Next runs:  AuthenticationRecord loaded → silent refresh → no browser
        Token expiry: refresh token handles this (~90 days before re-login)
        """
        now = time.time()
        if self._token and now < self._token_expires - 60:
            return self._token

        credential = self._get_credential()

        # If this is the first time (no auth record on disk), use
        # authenticate() which returns the AuthenticationRecord AND
        # gets the token in one shot.
        has_auth_record = self._AUTH_RECORD_FILE.exists()

        if not has_auth_record:
            logger.info("No auth record found — browser login required (one time only)")
            auth_record = credential.authenticate(scopes=[FABRIC_SCOPE])
            token_obj = credential.get_token(FABRIC_SCOPE)
            claims = self._decode_jwt_claims(token_obj.token)
            upn = claims.get("upn", claims.get("preferred_username", ""))

            if not self._is_azr_account(upn):
                logger.warning(
                    "Signed in as '%s' (not an _AZR account). Retrying...", upn
                )
                # Force a new interactive login with hint
                interactive = self._build_interactive_credential(login_hint=None)
                auth_record = interactive.authenticate(scopes=[FABRIC_SCOPE])
                token_obj = interactive.get_token(FABRIC_SCOPE)
                claims = self._decode_jwt_claims(token_obj.token)
                upn = claims.get("upn", claims.get("preferred_username", ""))
                credential = interactive

                if not self._is_azr_account(upn):
                    raise PermissionError(
                        f"Fabric requires an _AZR account. "
                        f"You signed in as '{upn}'. "
                        f"Please sign in with your _AZR account "
                        f"(e.g. yourname_azr@domain.com) and try again."
                    )

            # Save the auth record → all future calls will be silent
            self._save_auth_record(auth_record)
            self._credential = credential

        else:
            # Auth record exists → silent refresh (no browser)
            token_obj = credential.get_token(FABRIC_SCOPE)
            claims = self._decode_jwt_claims(token_obj.token)
            upn = claims.get("upn", claims.get("preferred_username", ""))

            if not self._is_azr_account(upn):
                # Cached record was for wrong account — clear and retry
                logger.warning(
                    "Cached auth is for '%s' (not _AZR). Clearing cache...", upn
                )
                self.clear_auth_cache()
                self._credential = None
                return self._get_token()  # recursive — will take the no-record path

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

    def request(
        self,
        method: str,
        url: str,
        json_body: Optional[Dict] = None,
        description: str = "",
    ) -> RestResult:
        """
        Public request wrapper.

        Accepts either a full Fabric API URL or a relative path beginning with `/`.
        This is useful for agents that need REST endpoints not yet modelled as
        dedicated helper methods.
        """
        resolved_url = url if url.startswith("http") else f"{FABRIC_API_BASE}{url}"
        return self._request(method, resolved_url, body=json_body, description=description)

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
    # Item definition CRUD (pipelines, notebooks, etc.)
    # ------------------------------------------------------------------
    def get_item_definition(
        self,
        workspace_id: str,
        item_id: str,
        item_type: Optional[str] = None,
    ) -> RestResult:
        """
        Get the definition (source content) of an item.

        Uses the ``POST .../getDefinition`` endpoint which returns the
        item's definition parts (e.g. pipeline-content.json for DataPipeline).

        Args:
            workspace_id: GUID of the workspace.
            item_id: GUID of the item.
            item_type: Optional Fabric item type for the URL path
                       (e.g. "dataPipelines", "notebooks"). If None, uses generic items endpoint.
        """
        if item_type:
            # Type-specific endpoint: /workspaces/{ws}/dataPipelines/{id}/getDefinition
            type_slug = self._item_type_to_slug(item_type)
            url = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/{type_slug}/{item_id}/getDefinition"
        else:
            url = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/items/{item_id}/getDefinition"

        return self._request("POST", url, description=f"getDefinition {item_id}")

    def update_item_definition(
        self,
        workspace_id: str,
        item_id: str,
        definition: Dict[str, Any],
        item_type: Optional[str] = None,
    ) -> RestResult:
        """
        Update the definition (source content) of an item.

        Uses the ``POST .../updateDefinition`` endpoint. The definition
        payload should contain ``{"definition": {"parts": [...]}}``.

        Args:
            workspace_id: GUID of the workspace.
            item_id: GUID of the item.
            definition: The definition payload with ``parts`` array.
            item_type: Optional Fabric item type for the URL path.
        """
        if item_type:
            type_slug = self._item_type_to_slug(item_type)
            url = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/{type_slug}/{item_id}/updateDefinition"
        else:
            url = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/items/{item_id}/updateDefinition"

        return self._request("POST", url, body=definition, description=f"updateDefinition {item_id}")

    @staticmethod
    def _item_type_to_slug(item_type: str) -> str:
        """
        Convert a Fabric item type to the REST API URL slug.

        E.g. "DataPipeline" → "dataPipelines", "Lakehouse" → "lakehouses"
        """
        slug_map = {
            "DataPipeline": "dataPipelines",
            "Notebook": "notebooks",
            "Lakehouse": "lakehouses",
            "Warehouse": "warehouses",
            "SemanticModel": "semanticModels",
            "Report": "reports",
            "SQLEndpoint": "sqlEndpoints",
            "SparkJobDefinition": "sparkJobDefinitions",
            "DataflowGen2": "dataflowsGen2",
            "MirroredDatabase": "mirroredDatabases",
        }
        return slug_map.get(item_type, f"{item_type[0].lower()}{item_type[1:]}s")

    # ------------------------------------------------------------------
    # Item discovery — find items by name across workspaces
    # ------------------------------------------------------------------
    def find_item_by_name(
        self,
        display_name: str,
        workspace_id: Optional[str] = None,
        item_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Find a Fabric item by its display name.

        Searches within a single workspace (if workspace_id given) or across
        all accessible workspaces. Returns the first match with full metadata
        including workspace_id, item_id, displayName, type.

        Args:
            display_name: The display name to search for (case-insensitive).
            workspace_id: Optional workspace GUID to search in.
            item_type: Optional item type filter (e.g. "Lakehouse").

        Returns:
            Dict with item metadata, or None if not found.
        """
        name_lower = display_name.lower()

        if workspace_id:
            # Search in a specific workspace
            result = self.list_items(workspace_id, item_type)
            if result.success:
                items = result.data if isinstance(result.data, list) else []
                for item in items:
                    if item.get("displayName", "").lower() == name_lower:
                        item["workspace_id"] = workspace_id
                        return item
            return None

        # Search across all accessible workspaces
        ws_result = self.list_workspaces()
        if not ws_result.success:
            return None

        workspaces = ws_result.data if isinstance(ws_result.data, list) else []
        for ws in workspaces:
            ws_id = ws.get("id", "")
            result = self.list_items(ws_id, item_type)
            if result.success:
                items = result.data if isinstance(result.data, list) else []
                for item in items:
                    if item.get("displayName", "").lower() == name_lower:
                        item["workspace_id"] = ws_id
                        item["workspace_name"] = ws.get("displayName", "")
                        return item

        return None

    def find_items_by_name(
        self,
        display_name: str,
        item_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find ALL Fabric items matching a display name across all workspaces.

        Returns a list of matches (there may be duplicates across workspaces).
        """
        name_lower = display_name.lower()
        matches: List[Dict[str, Any]] = []

        ws_result = self.list_workspaces()
        if not ws_result.success:
            return matches

        workspaces = ws_result.data if isinstance(ws_result.data, list) else []
        for ws in workspaces:
            ws_id = ws.get("id", "")
            result = self.list_items(ws_id, item_type)
            if result.success:
                items = result.data if isinstance(result.data, list) else []
                for item in items:
                    if item.get("displayName", "").lower() == name_lower:
                        item["workspace_id"] = ws_id
                        item["workspace_name"] = ws.get("displayName", "")
                        matches.append(item)

        return matches

    # ------------------------------------------------------------------
    # Workspace role assignments (who has access?)
    # ------------------------------------------------------------------
    def get_workspace_role_assignments(self, workspace_id: str) -> RestResult:
        """Get role assignments (access list) for a workspace."""
        return self._paginated_get(
            f"{FABRIC_API_BASE}/workspaces/{workspace_id}/roleAssignments",
            description=f"get role assignments for workspace {workspace_id}",
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
