"""
fabric_rest_client.py — Microsoft Fabric REST API Client
==========================================================
Uses Azure Identity (DefaultAzureCredential) so it shares the same
authentication as VS Code / Azure extensions. No separate `fab auth login`
required.

Fabric REST API base: https://api.fabric.microsoft.com/v1

This client covers the core CRUD operations that agents need:
    - Create / Update / Delete items
    - List items in a workspace
    - Get item details

Reference: https://learn.microsoft.com/en-us/rest/api/fabric/core/items
"""

from __future__ import annotations

import json
import logging
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


class FabricRestClient:
    """
    REST client for Microsoft Fabric using Azure Identity.

    Authentication precedence (via DefaultAzureCredential):
    1. Environment variables (AZURE_CLIENT_ID, etc.)
    2. Managed Identity
    3. VS Code / Azure CLI signed-in user  <-- this is what makes it work
    4. Azure PowerShell
    5. Interactive browser (fallback)

    This means if you're signed into Azure in VS Code, it Just Works™.
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
        self._workspace_name_cache: Dict[str, str] = {}  # name -> id

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def _get_credential(self):
        """Lazy-init Azure credential."""
        if self._credential is None:
            try:
                from azure.identity import DefaultAzureCredential
                self._credential = DefaultAzureCredential()
                logger.info("Azure DefaultAzureCredential initialized")
            except ImportError:
                logger.error(
                    "azure-identity not installed. Run: pip install azure-identity"
                )
                raise
        return self._credential

    def _get_token(self) -> str:
        """Get a valid access token, refreshing if expired."""
        now = time.time()
        if self._token and now < self._token_expires - 60:
            return self._token

        credential = self._get_credential()
        token = credential.get_token(FABRIC_SCOPE)
        self._token = token.token
        self._token_expires = token.expires_on
        logger.debug("Fabric token acquired, expires at %s", token.expires_on)
        return self._token

    def _headers(self) -> Dict[str, str]:
        """Build request headers with auth token."""
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

    def check_auth(self) -> bool:
        """Test if authentication works."""
        try:
            self._get_token()
            return True
        except Exception as exc:
            logger.error("Auth check failed: %s", exc)
            return False

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
