"""
MonitoringAgent — Governance / Platform Observability Agent
==============================================================
Platform observability, health monitoring, job tracking, and diagnostics
across all Fabric item types in a workspace.

Capabilities:
- List recent job runs (succeeded, failed, in-progress) for any workspace
- Get failed jobs with error details for triage
- Get item refresh history (pipelines, notebooks, lakehouses)
- Get capacity utilisation and throttling status
- Workspace health summary (item counts, last-run timestamps, failures)
- On-demand item run (trigger pipeline / notebook / dataflow refresh)

Item: Monitoring (MON)
REST:
  GET  /workspaces/{wsId}/items/{itemId}/jobs/instances
  GET  /workspaces/{wsId}/items/{itemId}/jobs/instances?status=Failed
  POST /workspaces/{wsId}/items/{itemId}/jobs/instances?jobType=Pipeline
  GET  /capacities/{capId}
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType

logger = logging.getLogger(__name__)


class MonitoringAgent(BaseAgent):
    """Platform observability, health monitoring, job tracking, and diagnostics."""

    ITEM_TYPE = "Monitoring"
    ITEM_CODE = "MON"
    FAB_NOUN = "monitoring"
    AGENT_FOLDER_NAME = "monitoring-agent"
    ALIASES = [
        "health",
        "diagnostics",
        "job_history",
        "failed_jobs",
        "refresh_history",
        "capacity_metrics",
        "platform_health",
    ]

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _rest(self):
        """Lazy-load the shared FabricRestClient."""
        if not hasattr(self, "_rest_client") or self._rest_client is None:
            from fabric_mas.core.fabric_rest_client import FabricRestClient
            self._rest_client = FabricRestClient()
        return self._rest_client

    def _ws(self, params: Dict[str, Any]) -> str:
        """Resolve workspace_id from params or fall back to default."""
        return params.get("workspace_id") or self.workspace_id

    def _job_instances_url(self, workspace_id: str, item_id: str) -> str:
        return f"/workspaces/{workspace_id}/items/{item_id}/jobs/instances"

    # ------------------------------------------------------------------ #
    # Core operations
    # ------------------------------------------------------------------ #
    def create(self, params: Dict[str, Any]) -> AgentResult:
        """
        Trigger an on-demand job run for a Fabric item.

        Expected params:
            workspace_id (optional): Target workspace GUID
            item_id (str): The item to trigger
            job_type (str): Pipeline | RunNotebook | DefaultJob (default: DefaultJob)
        """
        self._autotrain("create")
        ws = self._ws(params)
        item_id = params.get("item_id", "")
        job_type = params.get("job_type", "DefaultJob")

        if not item_id:
            return AgentResult(
                success=False, operation=OperationType.CREATE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message="item_id is required to trigger a job run.",
                errors=["Missing item_id"],
            )

        url = self._job_instances_url(ws, item_id)
        body = {"executionData": {}}  # minimal payload
        result = self._rest().request("POST", f"{url}?jobType={job_type}", json_body=body)

        if result.success:
            return AgentResult(
                success=True, operation=OperationType.CREATE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message=f"Job run triggered for item '{item_id}' (type={job_type}).",
                data=result.data if isinstance(result.data, dict) else {"raw": result.data},
            )
        return AgentResult(
            success=False, operation=OperationType.CREATE,
            agent_name=self.agent_name, item_type=self.ITEM_TYPE,
            message=f"Failed to trigger job: {result.error}",
            errors=[result.error],
        )

    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult:
        """
        Cancel a running job instance.

        Expected params:
            workspace_id (optional): Target workspace GUID
            item_id already provided via positional arg
            job_instance_id (str): The running job instance to cancel
        """
        self._autotrain("update")
        ws = self._ws(params)
        job_instance_id = params.get("job_instance_id", "")

        if not job_instance_id:
            return AgentResult(
                success=False, operation=OperationType.UPDATE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message="job_instance_id is required to cancel a job.",
                errors=["Missing job_instance_id"],
            )

        url = f"{self._job_instances_url(ws, item_id)}/{job_instance_id}/cancel"
        result = self._rest().request("POST", url)

        if result.success:
            return AgentResult(
                success=True, operation=OperationType.UPDATE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message=f"Job instance '{job_instance_id}' cancelled.",
                data={"item_id": item_id, "job_instance_id": job_instance_id},
            )
        return AgentResult(
            success=False, operation=OperationType.UPDATE,
            agent_name=self.agent_name, item_type=self.ITEM_TYPE,
            message=f"Failed to cancel job: {result.error}",
            errors=[result.error],
        )

    def delete(self, item_id: str) -> AgentResult:
        """
        Monitoring doesn't delete items — returns guidance.
        """
        self._autotrain("delete")
        return AgentResult(
            success=False, operation=OperationType.DELETE,
            agent_name=self.agent_name, item_type=self.ITEM_TYPE,
            message="Monitoring agent doesn't delete items. Use the item-specific agent "
                    "(e.g. data-pipeline, notebook) to delete Fabric items.",
            errors=["Not applicable for monitoring"],
        )

    def analyze(self, item_id: Optional[str] = None, **kwargs: Any) -> AgentResult:
        """
        Main monitoring entry point — flexible analysis operations.

        Supported analysis modes (via kwargs):
            mode="job_history"       → List recent job runs for an item
            mode="failed_jobs"       → List failed jobs in a workspace
            mode="workspace_health"  → Workspace health summary
            mode="refresh_history"   → Refresh history for pipeline / notebook / lakehouse
            mode="capacity"          → Capacity utilisation info

        Default: workspace_health if no item_id, job_history if item_id given.
        """
        self._autotrain("analyze")
        ws = kwargs.get("workspace_id") or self.workspace_id
        mode = kwargs.get("mode", "job_history" if item_id else "workspace_health")

        if mode == "job_history":
            return self._get_job_history(ws, item_id, **kwargs)
        elif mode == "failed_jobs":
            return self._get_failed_jobs(ws, **kwargs)
        elif mode == "workspace_health":
            return self._get_workspace_health(ws, **kwargs)
        elif mode == "refresh_history":
            return self._get_refresh_history(ws, item_id, **kwargs)
        elif mode == "capacity":
            return self._get_capacity_info(ws, **kwargs)
        else:
            return AgentResult(
                success=False, operation=OperationType.ANALYZE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message=f"Unknown analysis mode: '{mode}'. Supported: "
                        "job_history, failed_jobs, workspace_health, refresh_history, capacity.",
                errors=[f"Invalid mode: {mode}"],
            )

    def deploy(self, item_id: str, target: str, **kwargs: Any) -> AgentResult:
        """
        Monitoring doesn't deploy items — returns guidance.
        """
        self._autotrain("deploy")
        return AgentResult(
            success=False, operation=OperationType.DEPLOY,
            agent_name=self.agent_name, item_type=self.ITEM_TYPE,
            message="Monitoring agent doesn't deploy items. Use deployment-pipeline agent instead.",
            errors=["Not applicable for monitoring"],
        )

    # ------------------------------------------------------------------ #
    # Analysis implementations
    # ------------------------------------------------------------------ #
    def _get_job_history(
        self, workspace_id: str, item_id: Optional[str] = None, **kwargs
    ) -> AgentResult:
        """Get job history for a specific item."""
        if not item_id:
            return AgentResult(
                success=False, operation=OperationType.ANALYZE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message="item_id required for job_history. Use mode='failed_jobs' for workspace-wide scan.",
                errors=["Missing item_id"],
            )

        url = self._job_instances_url(workspace_id, item_id)
        result = self._rest().request("GET", url)

        if result.success:
            jobs = result.data if isinstance(result.data, list) else result.data.get("value", [])
            summary = {
                "item_id": item_id,
                "workspace_id": workspace_id,
                "total_jobs": len(jobs),
                "succeeded": sum(1 for j in jobs if j.get("status") == "Completed"),
                "failed": sum(1 for j in jobs if j.get("status") == "Failed"),
                "in_progress": sum(1 for j in jobs if j.get("status") == "InProgress"),
                "cancelled": sum(1 for j in jobs if j.get("status") == "Cancelled"),
                "recent_jobs": jobs[:10],  # Last 10
            }
            return AgentResult(
                success=True, operation=OperationType.ANALYZE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message=f"Job history: {summary['total_jobs']} runs — "
                        f"{summary['succeeded']} OK, {summary['failed']} failed, "
                        f"{summary['in_progress']} running.",
                data=summary,
            )
        return AgentResult(
            success=False, operation=OperationType.ANALYZE,
            agent_name=self.agent_name, item_type=self.ITEM_TYPE,
            message=f"Failed to get job history: {result.error}",
            errors=[result.error],
        )

    def _get_failed_jobs(self, workspace_id: str, **kwargs) -> AgentResult:
        """Scan all items in a workspace for recent failed jobs."""
        # Step 1: List all items in workspace
        items_result = self._rest().list_items(workspace_id)
        if not items_result.success:
            return AgentResult(
                success=False, operation=OperationType.ANALYZE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message=f"Failed to list workspace items: {items_result.error}",
                errors=[items_result.error],
            )

        items = items_result.data if isinstance(items_result.data, list) else items_result.data.get("value", [])

        # Step 2: For schedulable item types, check job history
        schedulable = {"DataPipeline", "Notebook", "SemanticModel", "DataflowGen2",
                       "SparkJobDefinition", "Lakehouse", "Warehouse"}
        failed_items: List[Dict[str, Any]] = []
        scanned = 0

        for item in items:
            if item.get("type") not in schedulable:
                continue
            scanned += 1
            iid = item.get("id", "")
            url = self._job_instances_url(workspace_id, iid)
            jr = self._rest().request("GET", url)
            if not jr.success:
                continue
            jobs = jr.data if isinstance(jr.data, list) else jr.data.get("value", [])
            failures = [j for j in jobs if j.get("status") == "Failed"]
            if failures:
                failed_items.append({
                    "item_id": iid,
                    "item_name": item.get("displayName", "?"),
                    "item_type": item.get("type", "?"),
                    "failure_count": len(failures),
                    "last_failure": failures[0] if failures else None,
                })

        summary = {
            "workspace_id": workspace_id,
            "items_scanned": scanned,
            "items_with_failures": len(failed_items),
            "failed_items": failed_items,
        }
        return AgentResult(
            success=True, operation=OperationType.ANALYZE,
            agent_name=self.agent_name, item_type=self.ITEM_TYPE,
            message=f"Scanned {scanned} schedulable items — "
                    f"{len(failed_items)} have recent failures.",
            data=summary,
        )

    def _get_workspace_health(self, workspace_id: str, **kwargs) -> AgentResult:
        """Workspace health summary: item counts by type, failure overview."""
        items_result = self._rest().list_items(workspace_id)
        if not items_result.success:
            return AgentResult(
                success=False, operation=OperationType.ANALYZE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message=f"Failed to list workspace items: {items_result.error}",
                errors=[items_result.error],
            )

        items = items_result.data if isinstance(items_result.data, list) else items_result.data.get("value", [])

        # Count by type
        type_counts: Dict[str, int] = {}
        for item in items:
            t = item.get("type", "Unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

        # Get workspace metadata
        ws_result = self._rest().get_workspace(workspace_id)
        ws_name = "?"
        if ws_result.success and isinstance(ws_result.data, dict):
            ws_name = ws_result.data.get("displayName", workspace_id)

        summary = {
            "workspace_id": workspace_id,
            "workspace_name": ws_name,
            "total_items": len(items),
            "items_by_type": dict(sorted(type_counts.items())),
        }
        return AgentResult(
            success=True, operation=OperationType.ANALYZE,
            agent_name=self.agent_name, item_type=self.ITEM_TYPE,
            message=f"Workspace '{ws_name}': {len(items)} items across "
                    f"{len(type_counts)} types.",
            data=summary,
        )

    def _get_refresh_history(
        self, workspace_id: str, item_id: Optional[str] = None, **kwargs
    ) -> AgentResult:
        """Get refresh history — delegates to job_history with context."""
        if not item_id:
            return AgentResult(
                success=False, operation=OperationType.ANALYZE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message="item_id required for refresh_history.",
                errors=["Missing item_id"],
            )
        # Refresh history is the same endpoint as job history for the item
        return self._get_job_history(workspace_id, item_id, **kwargs)

    def _get_capacity_info(self, workspace_id: str, **kwargs) -> AgentResult:
        """Get capacity info for the workspace."""
        # Get workspace to find its capacity
        ws_result = self._rest().get_workspace(workspace_id)
        if not ws_result.success:
            return AgentResult(
                success=False, operation=OperationType.ANALYZE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message=f"Failed to get workspace info: {ws_result.error}",
                errors=[ws_result.error],
            )

        ws_data = ws_result.data if isinstance(ws_result.data, dict) else {}
        cap_id = ws_data.get("capacityId", "")

        if not cap_id:
            return AgentResult(
                success=True, operation=OperationType.ANALYZE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message="Workspace has no assigned capacity (shared/trial mode).",
                data={"workspace_id": workspace_id, "capacity": "none/trial"},
            )

        # Get capacity details
        cap_result = self._rest().request("GET", f"/capacities/{cap_id}")
        if cap_result.success:
            cap_data = cap_result.data if isinstance(cap_result.data, dict) else {}
            summary = {
                "workspace_id": workspace_id,
                "capacity_id": cap_id,
                "display_name": cap_data.get("displayName", "?"),
                "sku": cap_data.get("sku", "?"),
                "region": cap_data.get("region", "?"),
                "state": cap_data.get("state", "?"),
            }
            return AgentResult(
                success=True, operation=OperationType.ANALYZE,
                agent_name=self.agent_name, item_type=self.ITEM_TYPE,
                message=f"Capacity '{summary['display_name']}' ({summary['sku']}) "
                        f"in {summary['region']} — state: {summary['state']}.",
                data=summary,
            )
        return AgentResult(
            success=False, operation=OperationType.ANALYZE,
            agent_name=self.agent_name, item_type=self.ITEM_TYPE,
            message=f"Failed to get capacity info: {cap_result.error}",
            errors=[cap_result.error],
        )
