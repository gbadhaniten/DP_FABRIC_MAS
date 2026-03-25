"""MapVisualAgent -- Reporting/Power BI Agent. Geospatial map visuals for Power BI reports."""
from __future__ import annotations
import logging
from typing import Any, Dict, Optional
from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType
logger = logging.getLogger(__name__)

class MapVisualAgent(BaseAgent):
    """Geospatial map visuals for Power BI reports."""
    ITEM_TYPE = "MapVisual"
    ITEM_CODE = "MAP"
    FAB_NOUN = "map-visual"
    AGENT_FOLDER_NAME = "map-visual-agent"

    def create(self, params: Dict[str, Any]) -> AgentResult:
        self._autotrain("create")
        dn = params.get("display_name", "Untitled_MapVisual")
        ws = params.get("workspace_id", self.workspace_id)
        cmd = self._build_fab_command("create", display_name=dn, description=params.get("description",""), workspace_id=ws)
        r = self._run(cmd); r.operation = OperationType.CREATE
        if r.success: r.message = f"MapVisual '{dn}' created"; r.data = {"display_name": dn, "workspace_id": ws}
        return r

    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult:
        self._autotrain("update")
        cmd = self._build_fab_command("update", workspace_id=self.workspace_id, **params)
        r = self._run(cmd); r.operation = OperationType.UPDATE; return r

    def delete(self, item_id: str) -> AgentResult:
        self._autotrain("delete")
        cmd = self._build_fab_command("delete", workspace_id=self.workspace_id)
        r = self._run(cmd); r.operation = OperationType.DELETE; return r

    def analyze(self, item_id: Optional[str] = None, **kwargs: Any) -> AgentResult:
        self._autotrain("list")
        verb = "show" if item_id else "list"
        cmd = self._build_fab_command(verb, workspace_id=self.workspace_id)
        r = self._run(cmd); r.operation = OperationType.ANALYZE; return r

    def deploy(self, item_id: str, target: str, **kwargs: Any) -> AgentResult:
        self._autotrain("deploy")
        cmd = self._build_fab_command("deploy", workspace_id=self.workspace_id, target_workspace_id=target)
        r = self._run(cmd); r.operation = OperationType.DEPLOY; return r
