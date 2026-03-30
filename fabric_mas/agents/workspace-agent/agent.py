"""
WorkspaceAgent — Governance/Admin Agent
==========================================
Fabric workspace lifecycle: create, configure, manage access, capacity assignment.

Capabilities:
- List all accessible workspaces (REST)
- Resolve workspace name → ID
- List items within a workspace (by type)
- Get role assignments (who has access)
- Create, update, delete workspaces

Item: Workspace (WS)
CLI:  fab workspace <verb> [options]
REST: GET  /workspaces
      GET  /workspaces/{id}
      GET  /workspaces/{id}/items
      GET  /workspaces/{id}/roleAssignments
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType

logger = logging.getLogger(__name__)


class WorkspaceAgent(BaseAgent):
    """Fabric workspace lifecycle: create, configure, manage access, capacity assignment."""

    ITEM_TYPE = "Workspace"
    ITEM_CODE = "WS"
    FAB_NOUN = "workspace"
    AGENT_FOLDER_NAME = "workspace-agent"

    # ── CREATE ────────────────────────────────────────────────────────
    def create(self, params: Dict[str, Any]) -> AgentResult:
        """Create a new workspace."""
        self._autotrain("create")
        dn = params.get("display_name", "Untitled_Workspace")

        # REST: POST /workspaces
        if self.rest_client:
            body = {"displayName": dn}
            desc = params.get("description", "")
            if desc:
                body["description"] = desc
            from fabric_mas.core.fabric_rest_client import FABRIC_API_BASE
            result = self.rest_client._request(
                "POST", f"{FABRIC_API_BASE}/workspaces", body=body,
                description=f"create workspace '{dn}'",
            )
            if result.success:
                return AgentResult(
                    success=True, operation=OperationType.CREATE,
                    agent_name=self.__class__.__name__,
                    item_type=self.ITEM_TYPE,
                    message=f"Workspace '{dn}' created",
                    data=result.data or {},
                    cli_command="REST API: create workspace",
                    cli_output=json.dumps(result.data, indent=2, default=str),
                )
            return AgentResult(
                success=False, operation=OperationType.CREATE,
                agent_name=self.__class__.__name__,
                item_type=self.ITEM_TYPE,
                message=f"Failed to create workspace: {result.error}",
                errors=[result.error],
            )

        # CLI fallback
        ws = params.get("workspace_id", self.workspace_id)
        cmd = self._build_fab_command(
            "create", display_name=dn,
            description=params.get("description", ""), workspace_id=ws,
        )
        r = self._run(cmd)
        r.operation = OperationType.CREATE
        if r.success:
            r.message = f"Workspace '{dn}' created"
            r.data = {"display_name": dn, "workspace_id": ws}
        return r

    # ── UPDATE ────────────────────────────────────────────────────────
    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult:
        """Update a workspace (display name, description)."""
        self._autotrain("update")

        if self.rest_client and item_id:
            from fabric_mas.core.fabric_rest_client import FABRIC_API_BASE
            body = {}
            if "display_name" in params:
                body["displayName"] = params["display_name"]
            if "description" in params:
                body["description"] = params["description"]
            result = self.rest_client._request(
                "PATCH", f"{FABRIC_API_BASE}/workspaces/{item_id}", body=body,
                description=f"update workspace {item_id}",
            )
            op_type = OperationType.UPDATE
            if result.success:
                return AgentResult(
                    success=True, operation=op_type,
                    agent_name=self.__class__.__name__,
                    item_type=self.ITEM_TYPE,
                    message=f"Workspace updated",
                    data=result.data or {},
                )
            return AgentResult(
                success=False, operation=op_type,
                agent_name=self.__class__.__name__,
                item_type=self.ITEM_TYPE,
                message=f"Failed to update workspace: {result.error}",
                errors=[result.error],
            )

        cmd = self._build_fab_command("update", workspace_id=self.workspace_id, **params)
        r = self._run(cmd)
        r.operation = OperationType.UPDATE
        return r

    # ── DELETE ────────────────────────────────────────────────────────
    def delete(self, item_id: str) -> AgentResult:
        """Delete a workspace."""
        self._autotrain("delete")

        if self.rest_client and item_id:
            from fabric_mas.core.fabric_rest_client import FABRIC_API_BASE
            result = self.rest_client._request(
                "DELETE", f"{FABRIC_API_BASE}/workspaces/{item_id}",
                description=f"delete workspace {item_id}",
            )
            if result.success:
                return AgentResult(
                    success=True, operation=OperationType.DELETE,
                    agent_name=self.__class__.__name__,
                    item_type=self.ITEM_TYPE,
                    message=f"Workspace {item_id} deleted",
                )
            return AgentResult(
                success=False, operation=OperationType.DELETE,
                agent_name=self.__class__.__name__,
                item_type=self.ITEM_TYPE,
                message=f"Failed to delete workspace: {result.error}",
                errors=[result.error],
            )

        cmd = self._build_fab_command("delete", workspace_id=self.workspace_id)
        r = self._run(cmd)
        r.operation = OperationType.DELETE
        return r

    # ── ANALYZE ───────────────────────────────────────────────────────
    def analyze(self, item_id: Optional[str] = None, **kwargs: Any) -> AgentResult:
        """
        Analyze workspaces: list all, list items in workspace, get role assignments.

        Supports kwargs:
            list_items=True, item_type="Lakehouse"  → list items in workspace
            role_assignments=True                     → get who has access
            (default)                                 → list all workspaces
        """
        self._autotrain("list")

        if not self.rest_client:
            verb = "show" if item_id else "list"
            cmd = self._build_fab_command(verb, workspace_id=self.workspace_id)
            r = self._run(cmd)
            r.operation = OperationType.ANALYZE
            return r

        # ── Role assignments ──
        if kwargs.get("role_assignments"):
            ws = self._resolve_workspace(kwargs.get("workspace_id") or item_id)
            if not ws:
                return self._make_result(
                    OperationType.ANALYZE, False,
                    "workspace_id required for role assignments",
                )
            result = self.rest_client.get_workspace_role_assignments(ws)
            if result.success:
                return AgentResult(
                    success=True, operation=OperationType.ANALYZE,
                    agent_name=self.__class__.__name__,
                    item_type=self.ITEM_TYPE,
                    message=f"Role assignments for workspace {ws}",
                    data={"role_assignments": result.data} if isinstance(result.data, list) else result.data,
                    cli_output=json.dumps(result.data, indent=2, default=str),
                )

        # ── List items in workspace ──
        if kwargs.get("list_items"):
            ws = self._resolve_workspace(kwargs.get("workspace_id") or item_id)
            if not ws:
                return self._make_result(
                    OperationType.ANALYZE, False,
                    "workspace_id required for list_items",
                )
            item_type = kwargs.get("item_type")
            result = self.rest_client.list_items(ws, item_type)
            if result.success:
                items = result.data if isinstance(result.data, list) else []
                return AgentResult(
                    success=True, operation=OperationType.ANALYZE,
                    agent_name=self.__class__.__name__,
                    item_type=self.ITEM_TYPE,
                    message=f"Found {len(items)} items in workspace {ws}"
                            + (f" (type={item_type})" if item_type else ""),
                    data={"items": items, "count": len(items)},
                    cli_output=json.dumps(items, indent=2, default=str),
                )

        # ── Resolve workspace by name ──
        if kwargs.get("resolve_name"):
            ws_name = kwargs.get("workspace_name") or kwargs.get("display_name")
            if ws_name:
                ws_id = self.rest_client.resolve_workspace_id(ws_name)
                if ws_id:
                    return AgentResult(
                        success=True, operation=OperationType.ANALYZE,
                        agent_name=self.__class__.__name__,
                        item_type=self.ITEM_TYPE,
                        message=f"Workspace '{ws_name}' resolved to ID: {ws_id}",
                        data={"workspace_name": ws_name, "workspace_id": ws_id},
                    )
                return self._make_result(
                    OperationType.ANALYZE, False,
                    f"Workspace '{ws_name}' not found",
                )

        # ── Default: list all workspaces ──
        result = self.rest_client.list_workspaces()
        if result.success:
            workspaces = result.data if isinstance(result.data, list) else []
            return AgentResult(
                success=True, operation=OperationType.ANALYZE,
                agent_name=self.__class__.__name__,
                item_type=self.ITEM_TYPE,
                message=f"Found {len(workspaces)} accessible workspaces",
                data={"workspaces": workspaces, "count": len(workspaces)},
                cli_output=json.dumps(workspaces, indent=2, default=str),
            )

        return self._make_result(
            OperationType.ANALYZE, False,
            f"Failed to list workspaces: {result.error}",
        )

    # ── DEPLOY ────────────────────────────────────────────────────────
    def deploy(self, item_id: str, target: str, **kwargs: Any) -> AgentResult:
        """Deploy workspace settings to another workspace."""
        self._autotrain("deploy")
        cmd = self._build_fab_command(
            "deploy", workspace_id=self.workspace_id, target_workspace_id=target,
        )
        r = self._run(cmd)
        r.operation = OperationType.DEPLOY
        return r
