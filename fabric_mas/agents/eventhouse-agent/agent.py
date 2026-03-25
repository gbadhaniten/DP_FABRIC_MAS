"""
EventhouseAgent — Real-Time Intelligence Agent
==================================================
Managed Kusto cluster hosting one or more KQL databases for event analytics.

Item: Eventhouse (EH)
CLI:  fab eventhouse <verb> [options]
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType

logger = logging.getLogger(__name__)


class EventhouseAgent(BaseAgent):
    """Managed Kusto cluster hosting one or more KQL databases for event analytics."""

    ITEM_TYPE = "Eventhouse"
    ITEM_CODE = "EH"
    FAB_NOUN = "eventhouse"
    AGENT_FOLDER_NAME = "eventhouse-agent"

    # ── CREATE ────────────────────────────────────────────────────────
    def create(self, params: Dict[str, Any]) -> AgentResult:
        """Create a new Eventhouse in the workspace."""
        self._autotrain("create")
        display_name = params.get("display_name", "Untitled_Eventhouse")
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
            result.message = f"Eventhouse '{display_name}' created in workspace {ws}"
            result.data = {"display_name": display_name, "workspace_id": ws}
        return result

    # ── UPDATE ────────────────────────────────────────────────────────
    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult:
        """Update an existing Eventhouse."""
        self._autotrain("update")
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
        """Delete a Eventhouse."""
        self._autotrain("delete")
        cmd = self._build_fab_command(
            "delete",
            workspace_id=self.workspace_id,
        )
        result = self._run(cmd)
        result.operation = OperationType.DELETE
        return result

    # ── ANALYZE ───────────────────────────────────────────────────────
    def analyze(self, item_id: Optional[str] = None, **kwargs: Any) -> AgentResult:
        """List or inspect Eventhouse items."""
        self._autotrain("list")
        verb = "show" if item_id else "list"
        cmd = self._build_fab_command(verb, workspace_id=self.workspace_id)
        result = self._run(cmd)
        result.operation = OperationType.ANALYZE
        return result

    # ── DEPLOY ────────────────────────────────────────────────────────
    def deploy(self, item_id: str, target: str, **kwargs: Any) -> AgentResult:
        """Deploy Eventhouse to a target workspace."""
        self._autotrain("deploy")
        cmd = self._build_fab_command(
            "deploy",
            workspace_id=self.workspace_id,
            target_workspace_id=target,
        )
        result = self._run(cmd)
        result.operation = OperationType.DEPLOY
        return result
