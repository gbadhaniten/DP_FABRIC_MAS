"""
DataPipelineAgent — Data Integration Agent
==============================================
ETL orchestration pipelines with activities, triggers, and monitoring.

Capabilities:
- Create pipelines (REST-first, CLI fallback)
- Create pipelines with Copy Activity (cross-workspace Lakehouse-to-Lakehouse)
- Update pipeline definitions (add/modify activities)
- Resolve items by name across workspaces for source/sink configuration
- Delete by name or by ID

Item: DataPipeline (DP)
CLI:  fab data-pipeline <verb> [options]
REST: POST /workspaces/{wsId}/items  (type: DataPipeline)
      POST /workspaces/{wsId}/dataPipelines/{id}/getDefinition
      POST /workspaces/{wsId}/dataPipelines/{id}/updateDefinition
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any, Dict, List, Optional

from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType

logger = logging.getLogger(__name__)


class DataPipelineAgent(BaseAgent):
    """ETL orchestration pipelines with activities, triggers, and monitoring."""

    ITEM_TYPE = "DataPipeline"
    ITEM_CODE = "DP"
    FAB_NOUN = "data-pipeline"
    AGENT_FOLDER_NAME = "data-pipeline-agent"

    # ------------------------------------------------------------------
    # Pipeline Definition Builder (static helpers)
    # ------------------------------------------------------------------
    @staticmethod
    def build_copy_activity(
        activity_name: str,
        source_workspace_id: str,
        source_item_id: str,
        sink_workspace_id: str,
        sink_item_id: str,
        source_type: str = "LakehouseTable",
        sink_type: str = "LakehouseTable",
        table_action: str = "Append",
    ) -> Dict[str, Any]:
        """
        Build a Copy Activity JSON structure for a Fabric pipeline.

        Supports cross-workspace Lakehouse-to-Lakehouse copy (the most
        common pattern). Can be extended for other source/sink types.

        Args:
            activity_name: Display name of the copy activity.
            source_workspace_id: GUID of the source workspace.
            source_item_id: GUID of the source item (e.g. Lakehouse).
            sink_workspace_id: GUID of the sink/target workspace.
            sink_item_id: GUID of the sink/target item.
            source_type: Source dataset type (default: LakehouseTable).
            sink_type: Sink dataset type (default: LakehouseTable).
            table_action: Sink table action: Append, Overwrite (default: Append).

        Returns:
            Dict representing the Copy Activity in Fabric pipeline JSON format.
        """

        def _lakehouse_dataset(workspace_id: str, item_id: str, ds_type: str) -> Dict:
            return {
                "type": ds_type,
                "typeProperties": {},
                "linkedService": {
                    "properties": {
                        "type": "Lakehouse",
                        "typeProperties": {
                            "workspaceId": workspace_id,
                            "artifactId": item_id,
                        },
                    },
                },
                "externalReferences": {
                    "connection": "builtin",
                },
            }

        source_linked = "Lakehouse" if "Lakehouse" in source_type else source_type
        sink_linked = "Lakehouse" if "Lakehouse" in sink_type else sink_type

        activity = {
            "name": activity_name,
            "type": "Copy",
            "dependsOn": [],
            "policy": {
                "timeout": "0.12:00:00",
                "retry": 0,
                "retryIntervalInSeconds": 30,
                "secureInput": False,
                "secureOutput": False,
            },
            "typeProperties": {
                "source": {
                    "type": f"{source_type}Source"
                            if not source_type.endswith("Source")
                            else source_type,
                    "datasetSettings": _lakehouse_dataset(
                        source_workspace_id, source_item_id, source_type
                    ),
                },
                "sink": {
                    "type": f"{sink_type}Sink"
                          if not sink_type.endswith("Sink")
                          else sink_type,
                    "tableActionOption": table_action,
                    "datasetSettings": _lakehouse_dataset(
                        sink_workspace_id, sink_item_id, sink_type
                    ),
                },
                "enableStaging": False,
            },
        }
        return activity

    @staticmethod
    def build_pipeline_definition(
        activities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build a complete pipeline definition payload ready for updateDefinition API.

        Args:
            activities: List of activity dicts (e.g. from build_copy_activity).

        Returns:
            Dict with the full updateDefinition body including base64-encoded
            pipeline-content.json.
        """
        pipeline_content = {
            "properties": {
                "activities": activities,
            }
        }
        content_bytes = json.dumps(pipeline_content).encode("utf-8")
        payload_b64 = base64.b64encode(content_bytes).decode("utf-8")

        return {
            "definition": {
                "parts": [
                    {
                        "path": "pipeline-content.json",
                        "payload": payload_b64,
                        "payloadType": "InlineBase64",
                    }
                ]
            }
        }

    # ------------------------------------------------------------------
    # Item resolution helpers
    # ------------------------------------------------------------------
    def _resolve_item(
        self,
        display_name: str,
        workspace: Optional[str] = None,
        item_type: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve an item by display name, optionally within a specific workspace.

        Args:
            display_name: Item name to find.
            workspace: Workspace name or ID (optional; searches all if None).
            item_type: Item type filter (e.g. "Lakehouse").

        Returns:
            Item metadata dict with id, displayName, workspace_id, etc.
        """
        if not self.rest_client:
            return None

        ws_id = None
        if workspace:
            ws_id = self.rest_client.resolve_workspace_id(workspace)

        return self.rest_client.find_item_by_name(display_name, ws_id, item_type)

    # ── CREATE ────────────────────────────────────────────────────────
    def create(self, params: Dict[str, Any]) -> AgentResult:
        """
        Create a new DataPipeline in the workspace.

        Supports two modes:
        1. Simple create: just creates an empty pipeline shell
        2. Create with copy activity: creates pipeline + configures Copy Activity
           Requires: source_workspace, source_item, sink_workspace, sink_item

        Params:
            display_name: Pipeline name (auto-corrected via naming convention)
            workspace_id: Target workspace (name or ID)
            description: Optional description
            source_workspace: Source workspace name or ID (for copy activity)
            source_item: Source item name (for copy activity)
            sink_workspace: Sink/target workspace name or ID (for copy activity)
            sink_item: Sink/target item name (for copy activity)
            source_type: Source item type (default: Lakehouse)
            sink_type: Sink item type (default: Lakehouse)
        """
        self._autotrain("create")
        display_name = params.get("display_name", "Untitled_DataPipeline")
        description = params.get("description", "")

        # ── Step 1: Create the pipeline shell via REST ──
        rest_result = self._run_rest("create", params)
        if rest_result is not None and rest_result.success:
            pipeline_data = rest_result.data or {}
            pipeline_id = pipeline_data.get("id", "")
            ws = self._resolve_workspace(params.get("workspace_id"))

            # ── Step 2: If source/sink specified, add Copy Activity ──
            source_item_name = params.get("source_item")
            sink_item_name = params.get("sink_item")

            if source_item_name and sink_item_name and pipeline_id:
                copy_result = self._configure_copy_activity(
                    pipeline_id=pipeline_id,
                    workspace_id=ws,
                    params=params,
                )
                if copy_result and copy_result.success:
                    rest_result.message = (
                        f"DataPipeline '{display_name}' created with Copy Activity "
                        f"({source_item_name} → {sink_item_name})"
                    )
                    rest_result.data["copy_activity"] = "configured"
                else:
                    rest_result.message = (
                        f"DataPipeline '{display_name}' created but Copy Activity "
                        f"configuration failed: {copy_result.message if copy_result else 'unknown error'}"
                    )
                    rest_result.data["copy_activity"] = "failed"
            else:
                rest_result.message = (
                    f"DataPipeline '{display_name}' created in workspace {ws}"
                )

            return rest_result

        if rest_result is not None:
            return rest_result

        # ── Fallback to CLI ──
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
            result.message = f"DataPipeline '{display_name}' created in workspace {ws}"
            result.data = {"display_name": display_name, "workspace_id": ws}
        return result

    def _configure_copy_activity(
        self,
        pipeline_id: str,
        workspace_id: str,
        params: Dict[str, Any],
    ) -> Optional[AgentResult]:
        """
        Configure a Copy Activity on an existing pipeline.

        Resolves source and sink items by name (cross-workspace), builds
        the pipeline definition, and calls updateDefinition API.
        """
        source_workspace = params.get("source_workspace")
        source_item_name = params.get("source_item", "")
        sink_workspace = params.get("sink_workspace")
        sink_item_name = params.get("sink_item", "")
        source_type = params.get("source_type", "Lakehouse")
        sink_type = params.get("sink_type", "Lakehouse")
        activity_name = params.get(
            "activity_name",
            f"Copy {source_item_name} to {sink_item_name}",
        )

        # Resolve source item
        source = self._resolve_item(source_item_name, source_workspace, source_type)
        if not source:
            return self._make_result(
                OperationType.CREATE, False,
                f"Source {source_type} '{source_item_name}' not found"
                + (f" in workspace '{source_workspace}'" if source_workspace else ""),
            )

        # Resolve sink item
        sink = self._resolve_item(sink_item_name, sink_workspace, sink_type)
        if not sink:
            return self._make_result(
                OperationType.CREATE, False,
                f"Sink {sink_type} '{sink_item_name}' not found"
                + (f" in workspace '{sink_workspace}'" if sink_workspace else ""),
            )

        logger.info(
            "Resolved source: %s/%s (ws=%s), sink: %s/%s (ws=%s)",
            source.get("displayName"), source.get("id"), source.get("workspace_id"),
            sink.get("displayName"), sink.get("id"), sink.get("workspace_id"),
        )

        # Build the Copy Activity
        copy_activity = self.build_copy_activity(
            activity_name=activity_name,
            source_workspace_id=source.get("workspace_id", ""),
            source_item_id=source.get("id", ""),
            sink_workspace_id=sink.get("workspace_id", ""),
            sink_item_id=sink.get("id", ""),
            source_type=f"{source_type}Table" if "Table" not in source_type else source_type,
            sink_type=f"{sink_type}Table" if "Table" not in sink_type else sink_type,
        )

        # Build definition payload
        definition = self.build_pipeline_definition([copy_activity])

        # Update the pipeline definition
        result = self.rest_client.update_item_definition(
            workspace_id, pipeline_id, definition, self.ITEM_TYPE
        )

        if result.success:
            return self._make_result(
                OperationType.CREATE, True,
                f"Copy Activity configured: {source_item_name} → {sink_item_name}",
                data={
                    "pipeline_id": pipeline_id,
                    "source": {
                        "name": source.get("displayName"),
                        "id": source.get("id"),
                        "workspace_id": source.get("workspace_id"),
                    },
                    "sink": {
                        "name": sink.get("displayName"),
                        "id": sink.get("id"),
                        "workspace_id": sink.get("workspace_id"),
                    },
                },
            )
        else:
            return self._make_result(
                OperationType.CREATE, False,
                f"Failed to update pipeline definition: {result.error}",
                errors=[result.error],
            )

    # ── UPDATE ────────────────────────────────────────────────────────
    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult:
        """Update an existing DataPipeline."""
        self._autotrain("update")

        # If definition is provided, use update_definition
        if "definition" in params or "activities" in params:
            activities = params.get("activities", [])
            if activities:
                definition = self.build_pipeline_definition(activities)
                params["definition"] = definition
                params["item_id"] = item_id
                rest_result = self._run_rest("update_definition", params)
                if rest_result is not None:
                    return rest_result

        # Standard metadata update
        rest_result = self._run_rest("update", {**params, "item_id": item_id})
        if rest_result is not None:
            return rest_result

        # CLI fallback
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
        """Delete a DataPipeline by ID or by name."""
        self._autotrain("delete")

        # If item_id looks like a name (not a GUID), try delete by name
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
        """List or inspect DataPipeline items."""
        self._autotrain("list")

        # Try REST first
        rest_result = self._run_rest("list" if not item_id else "analyze", {
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
        """Deploy DataPipeline to a target workspace."""
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
        import re
        return bool(re.match(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
            value,
        ))
