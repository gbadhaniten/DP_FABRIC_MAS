"""
SQLDatabaseAgent — Analytics/Warehousing Agent
==================================================
Fabric SQL Database for transactional OLTP workloads.

Item: SQLDatabase (SQLDB)
CLI:  fab sql-database <verb> [options]
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType

logger = logging.getLogger(__name__)


class SQLDatabaseAgent(BaseAgent):
    """Fabric SQL Database for transactional OLTP workloads."""

    ITEM_TYPE = "SQLDatabase"
    ITEM_CODE = "SQLDB"
    FAB_NOUN = "sql-database"
    AGENT_FOLDER_NAME = "sql-database-agent"

    # ── CREATE ────────────────────────────────────────────────────────
    def create(self, params: Dict[str, Any]) -> AgentResult:
        """Create a new SQLDatabase in the workspace."""
        self._autotrain("create")
        display_name = params.get("display_name", "Untitled_SQLDatabase")
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
            result.message = f"SQLDatabase '{display_name}' created in workspace {ws}"
            result.data = {"display_name": display_name, "workspace_id": ws}
        return result

    # ── UPDATE ────────────────────────────────────────────────────────
    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult:
        """Update an existing SQLDatabase."""
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
        """Delete a SQLDatabase."""
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
        """List or inspect SQLDatabase items."""
        self._autotrain("list")
        verb = "show" if item_id else "list"
        cmd = self._build_fab_command(verb, workspace_id=self.workspace_id)
        result = self._run(cmd)
        result.operation = OperationType.ANALYZE
        return result

    # ── DEPLOY ────────────────────────────────────────────────────────
    def deploy(self, item_id: str, target: str, **kwargs: Any) -> AgentResult:
        """Deploy SQLDatabase to a target workspace."""
        self._autotrain("deploy")
        cmd = self._build_fab_command(
            "deploy",
            workspace_id=self.workspace_id,
            target_workspace_id=target,
        )
        result = self._run(cmd)
        result.operation = OperationType.DEPLOY
        return result
