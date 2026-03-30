"""
CopyJobAgent — Data Integration Agent
=========================================
Bulk data copy between heterogeneous sources and Fabric destinations.

Capabilities:
- Create copy jobs (REST-first, CLI fallback)
- Delete by name or by ID
- List copy jobs via REST
- Cross-workspace item resolution

Item: CopyJob (CPJ)
CLI:  fab copy-job <verb> [options]
REST: POST /workspaces/{wsId}/items  (type: CopyJob)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType

logger = logging.getLogger(__name__)


class CopyJobAgent(BaseAgent):
    """Bulk data copy between heterogeneous sources and Fabric destinations."""

    ITEM_TYPE = "CopyJob"
    ITEM_CODE = "CPJ"
    FAB_NOUN = "copy-job"
    AGENT_FOLDER_NAME = "copy-job-agent"

    # ── CREATE ────────────────────────────────────────────────────────
    def create(self, params: Dict[str, Any]) -> AgentResult:
        """Create a new CopyJob in the workspace."""
        self._autotrain("create")

        # Try REST API first
        rest_result = self._run_rest("create", params)
        if rest_result is not None:
            if rest_result.success:
                rest_result.message = (
                    f"CopyJob '{params.get('display_name', '')}' created "
                    f"in workspace {params.get('workspace_id', self.workspace_id)}"
                )
            return rest_result

        # Fallback to CLI
        display_name = params.get("display_name", "Untitled_CopyJob")
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
            result.message = f"CopyJob '{display_name}' created in workspace {ws}"
            result.data = {"display_name": display_name, "workspace_id": ws}
        return result

    # ── UPDATE ────────────────────────────────────────────────────────
    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult:
        """Update an existing CopyJob."""
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
        """Delete a CopyJob by ID or by name."""
        self._autotrain("delete")

        # If item_id looks like a name, try delete by name
        if item_id and not self._is_guid(item_id):
            rest_result = self._run_rest("delete_by_name", {
                "display_name": item_id,
                "workspace_id": self.workspace_id,
            })
            if rest_result is not None:
                return rest_result

        rest_result = self._run_rest("delete", {
            "item_id": item_id,
            "workspace_id": self.workspace_id,
        })
        if rest_result is not None:
            return rest_result

        cmd = self._build_fab_command(
            "delete",
            workspace_id=self.workspace_id,
        )
        result = self._run(cmd)
        result.operation = OperationType.DELETE
        return result

    # ── ANALYZE ───────────────────────────────────────────────────────
    def analyze(self, item_id: Optional[str] = None, **kwargs: Any) -> AgentResult:
        """List or inspect CopyJob items."""
        self._autotrain("list")

        rest_result = self._run_rest("list", {
            "workspace_id": kwargs.get("workspace_id", self.workspace_id),
        })
        if rest_result is not None:
            return rest_result

        verb = "show" if item_id else "list"
        cmd = self._build_fab_command(verb, workspace_id=self.workspace_id)
        result = self._run(cmd)
        result.operation = OperationType.ANALYZE
        return result

    # ── DEPLOY ────────────────────────────────────────────────────────
    def deploy(self, item_id: str, target: str, **kwargs: Any) -> AgentResult:
        """Deploy CopyJob to a target workspace."""
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
