"""
LakehouseAgent — Data Engineering Agent
===========================================
Delta Lake storage with auto SQL endpoint. Core of Medallion architecture (Bronze/Silver/Gold).

Capabilities:
- Create lakehouses (REST-first, CLI fallback)
- Delete by name or by ID (auto-resolves name → ID via REST)
- Find/list lakehouses across workspaces
- Cross-workspace item resolution (used by pipeline agent for source/sink)

Item: Lakehouse (LH)
CLI:  fab lakehouse <verb> [options]
REST: POST /workspaces/{wsId}/items  (type: Lakehouse)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType

logger = logging.getLogger(__name__)


class LakehouseAgent(BaseAgent):
    """Delta Lake storage with auto SQL endpoint. Core of Medallion architecture (Bronze/Silver/Gold)."""

    ITEM_TYPE = "Lakehouse"
    ITEM_CODE = "LH"
    FAB_NOUN = "lakehouse"
    AGENT_FOLDER_NAME = "lakehouse-agent"

    # ── CREATE ────────────────────────────────────────────────────────
    def create(self, params: Dict[str, Any]) -> AgentResult:
        """Create a new Lakehouse in the workspace."""
        self._autotrain("create")

        # Try REST API first
        rest_result = self._run_rest("create", params)
        if rest_result is not None:
            if rest_result.success:
                rest_result.message = (
                    f"Lakehouse '{params.get('display_name', '')}' created "
                    f"in workspace {params.get('workspace_id', self.workspace_id)}"
                )
            return rest_result

        # Fallback to CLI
        display_name = params.get("display_name", "Untitled_Lakehouse")
        description = params.get("description", "")
        ws = params.get("workspace_id", self.workspace_id)

        cmd = self._build_fab_command(
            "create",
            display_name=display_name,
            description=description,
            workspace_id=ws,
        )
        result = self._run(cmd)
        result.operation = OperationType.CREATE
        if result.success:
            result.message = f"Lakehouse '{display_name}' created in workspace {ws}"
            result.data = {"display_name": display_name, "workspace_id": ws}
        return result

    # ── UPDATE ────────────────────────────────────────────────────────
    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult:
        """Update an existing Lakehouse."""
        self._autotrain("update")

        rest_result = self._run_rest("update", {**params, "item_id": item_id})
        if rest_result is not None:
            return rest_result

        cmd = self._build_fab_command(
            "update",
            workspace_id=self.workspace_id,
            **params,
        )
        result = self._run(cmd)
        result.operation = OperationType.UPDATE
        return result

    # ── DELETE ────────────────────────────────────────────────────────
    def delete(self, item_id: str) -> AgentResult:
        """
        Delete a Lakehouse by ID or by name.

        If item_id is not a GUID, treats it as a display name and
        auto-resolves to the actual ID via REST API.
        """
        self._autotrain("delete")

        # If item_id looks like a name (not a GUID), try delete by name
        if item_id and not self._is_guid(item_id):
            rest_result = self._run_rest("delete_by_name", {
                "display_name": item_id,
                "workspace_id": self.workspace_id,
            })
            if rest_result is not None:
                return rest_result

        # Delete by GUID
        rest_result = self._run_rest("delete", {
            "item_id": item_id,
            "workspace_id": self.workspace_id,
        })
        if rest_result is not None:
            return rest_result

        # CLI fallback
        cmd = self._build_fab_command(
            "delete",
            workspace_id=self.workspace_id,
        )
        result = self._run(cmd)
        result.operation = OperationType.DELETE
        return result

    # ── ANALYZE ───────────────────────────────────────────────────────
    def analyze(self, item_id: Optional[str] = None, **kwargs: Any) -> AgentResult:
        """List or inspect Lakehouse items."""
        self._autotrain("list")

        # If a display_name is given, find by name
        display_name = kwargs.get("display_name")
        if display_name:
            rest_result = self._run_rest("find_by_name", {
                "display_name": display_name,
                "workspace_id": kwargs.get("workspace_id", self.workspace_id),
            })
            if rest_result is not None:
                return rest_result

        # List all lakehouses in workspace
        rest_result = self._run_rest("list", {
            "workspace_id": kwargs.get("workspace_id", self.workspace_id),
        })
        if rest_result is not None:
            return rest_result

        # CLI fallback
        verb = "show" if item_id else "list"
        cmd = self._build_fab_command(verb, workspace_id=self.workspace_id)
        result = self._run(cmd)
        result.operation = OperationType.ANALYZE
        return result

    # ── DEPLOY ────────────────────────────────────────────────────────
    def deploy(self, item_id: str, target: str, **kwargs: Any) -> AgentResult:
        """Deploy Lakehouse to a target workspace."""
        self._autotrain("deploy")
        cmd = self._build_fab_command(
            "deploy",
            workspace_id=self.workspace_id,
            target_workspace_id=target,
        )
        result = self._run(cmd)
        result.operation = OperationType.DEPLOY
        return result

    # ── Helpers ────────────────────────────────────────────────────────
    @staticmethod
    def _is_guid(value: str) -> bool:
        """Check if a string looks like a GUID."""
        return bool(re.match(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
            value,
        ))
