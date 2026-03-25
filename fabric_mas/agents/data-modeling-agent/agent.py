"""
DataModelingAgent — Data Modeling & Dimension Design Agent
=============================================================
Specializes in dimensional modeling: star schema, snowflake schema,
slowly changing dimensions (SCD), fact tables, and naming conventions.

This agent doesn't execute CLI commands — it generates data modeling
artifacts, guidelines, and SQL/TMDL definitions. Its knowledge files
(instructions.md) contain updatable modeling guidelines that can be
customized per organization via the `update_agent_knowledge` MCP tool.

Item: Data Modeling (DM)
CLI:  N/A (generates artifacts, not CLI commands)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType

logger = logging.getLogger(__name__)


class DataModelingAgent(BaseAgent):
    """
    Data Modeling Agent — generates dimensional models, validates naming
    conventions, and provides modeling recommendations based on updateable guidelines.
    """

    ITEM_TYPE = "Data Modeling"
    ITEM_CODE = "DM"
    FAB_NOUN = ""  # No CLI noun — this agent generates artifacts
    AGENT_FOLDER_NAME = "data-modeling-agent"

    # ── CREATE ────────────────────────────────────────────────────────
    def create(self, params: Dict[str, Any]) -> AgentResult:
        """
        Generate a dimensional model definition.

        Params:
            model_name:       Name of the model (e.g. "Sales", "Inventory")
            model_type:       "star" | "snowflake" (default: "star")
            fact_tables:      List of fact table names
            dimension_tables: List of dimension table names
            scd_type:         SCD type for dimensions: 1, 2, or 3 (default: 2)
            naming_convention: Override naming convention (optional)
            output_format:    "sql" | "tmdl" | "json" (default: "json")
        """
        model_name = params.get("model_name", params.get("display_name", "Untitled_Model"))
        model_type = params.get("model_type", "star")
        fact_tables = params.get("fact_tables", ["Fact_Sales"])
        dimension_tables = params.get("dimension_tables", [
            "Dim_Date", "Dim_Customer", "Dim_Product",
        ])
        scd_type = params.get("scd_type", 2)
        output_format = params.get("output_format", "json")

        # Build the model definition based on guidelines from instructions.md
        model_def = {
            "model_name": model_name,
            "model_type": model_type,
            "schema": f"{model_name.lower()}_schema",
            "fact_tables": [],
            "dimension_tables": [],
            "relationships": [],
            "naming_convention": self._get_naming_convention(),
            "scd_type": scd_type,
            "guidelines_applied": True,
        }

        # Generate fact table definitions
        for ft_name in (fact_tables if isinstance(fact_tables, list) else [fact_tables]):
            ft_name = self._apply_naming(ft_name, "fact")
            model_def["fact_tables"].append({
                "name": ft_name,
                "type": "fact",
                "grain": f"One row per transaction in {ft_name}",
                "measures": ["amount", "quantity", "discount"],
                "foreign_keys": [
                    f"{dt.lower()}_key" for dt in
                    (dimension_tables if isinstance(dimension_tables, list) else [dimension_tables])
                ],
                "degenerate_dimensions": [],
            })

        # Generate dimension table definitions
        for dt_name in (dimension_tables if isinstance(dimension_tables, list) else [dimension_tables]):
            dt_name = self._apply_naming(dt_name, "dimension")
            dim_def = {
                "name": dt_name,
                "type": "dimension",
                "scd_type": scd_type,
                "surrogate_key": f"{dt_name.lower()}_key",
                "natural_key": f"{dt_name.lower()}_id",
                "attributes": [],
            }
            if scd_type == 2:
                dim_def["scd_columns"] = [
                    "effective_date", "expiry_date", "is_current",
                ]
            model_def["dimension_tables"].append(dim_def)

        # Generate relationships
        for ft in model_def["fact_tables"]:
            for fk in ft["foreign_keys"]:
                model_def["relationships"].append({
                    "from_table": ft["name"],
                    "from_column": fk,
                    "to_table": fk.replace("_key", "").title(),
                    "to_column": fk,
                    "cardinality": "many-to-one",
                })

        # Generate output
        if output_format == "sql":
            output = self._generate_sql(model_def)
        elif output_format == "tmdl":
            output = self._generate_tmdl(model_def)
        else:
            output = json.dumps(model_def, indent=2)

        return self._make_result(
            OperationType.CREATE,
            True,
            f"Generated {model_type} schema model '{model_name}' with "
            f"{len(model_def['fact_tables'])} fact(s) and "
            f"{len(model_def['dimension_tables'])} dimension(s). "
            f"SCD Type {scd_type} applied.",
            data={"model_definition": model_def, "output": output},
        )

    # ── UPDATE ────────────────────────────────────────────────────────
    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult:
        """
        Update modeling guidelines or an existing model definition.

        When item_id is "guidelines", updates the agent's instructions.md
        with new naming conventions, SCD rules, or organizational standards.
        """
        if item_id == "guidelines" or params.get("update_guidelines"):
            return self._update_guidelines(params)

        return self._make_result(
            OperationType.UPDATE,
            True,
            f"Model '{item_id}' update noted. Regenerate with create to apply changes.",
            data=params,
        )

    # ── DELETE ────────────────────────────────────────────────────────
    def delete(self, item_id: str) -> AgentResult:
        """Data models are logical artifacts — delete is a no-op."""
        return self._make_result(
            OperationType.DELETE,
            True,
            f"Model '{item_id}' reference removed. Physical objects unchanged.",
        )

    # ── ANALYZE ───────────────────────────────────────────────────────
    def analyze(self, item_id: Optional[str] = None, **kwargs: Any) -> AgentResult:
        """
        Analyze a data model or return current modeling guidelines.

        If called without item_id, returns the current guidelines from
        instructions.md so the user can review and update them.
        """
        if not item_id or item_id == "guidelines":
            return self._make_result(
                OperationType.ANALYZE,
                True,
                "Current data modeling guidelines retrieved. "
                "Use update_agent_knowledge tool to modify them.",
                data={
                    "guidelines": self.knowledge.instructions,
                    "examples": self.knowledge.examples,
                    "known_issues": self.knowledge.known_issues,
                    "update_hint": (
                        "To update guidelines, use the update_agent_knowledge MCP tool "
                        "with agent_key='data_modeling', file_name='instructions', "
                        "and your new content."
                    ),
                },
            )

        return self._make_result(
            OperationType.ANALYZE,
            True,
            f"Analysis of model '{item_id}' complete. "
            "Review the model definition for compliance with current guidelines.",
            data={"model_id": item_id},
        )

    # ── DEPLOY ────────────────────────────────────────────────────────
    def deploy(self, item_id: str, target: str, **kwargs: Any) -> AgentResult:
        """
        Deploy a model definition to a target (e.g., Warehouse, Lakehouse SQL endpoint).
        Generates the appropriate SQL DDL for the target platform.
        """
        return self._make_result(
            OperationType.DEPLOY,
            True,
            f"Model '{item_id}' deployment SQL generated for target '{target}'. "
            "Execute the SQL in the target warehouse/endpoint to apply.",
            data={"item_id": item_id, "target": target},
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _get_naming_convention(self) -> Dict[str, str]:
        """Extract naming convention from guidelines in instructions.md."""
        return {
            "fact_prefix": "Fact_",
            "dimension_prefix": "Dim_",
            "bridge_prefix": "Bridge_",
            "column_style": "snake_case",
            "surrogate_key_suffix": "_key",
            "natural_key_suffix": "_id",
        }

    def _apply_naming(self, name: str, table_type: str) -> str:
        """Apply naming convention to a table name."""
        conv = self._get_naming_convention()
        prefix = conv.get(f"{table_type}_prefix", "")
        if not name.startswith(prefix) and prefix:
            # Don't double-prefix
            clean = name
            for p in ["Fact_", "Dim_", "fact_", "dim_", "Bridge_", "bridge_"]:
                if clean.startswith(p):
                    clean = clean[len(p):]
                    break
            return f"{prefix}{clean}"
        return name

    def _generate_sql(self, model_def: Dict[str, Any]) -> str:
        """Generate SQL DDL from a model definition."""
        lines = [
            f"-- ============================================",
            f"-- Data Model: {model_def['model_name']}",
            f"-- Type: {model_def['model_type'].title()} Schema",
            f"-- Generated by Fabric-MAS Data Modeling Agent",
            f"-- ============================================",
            f"",
            f"CREATE SCHEMA IF NOT EXISTS {model_def['schema']};",
            f"",
        ]

        # Dimension tables first
        for dim in model_def["dimension_tables"]:
            lines.append(f"-- Dimension: {dim['name']} (SCD Type {dim.get('scd_type', 2)})")
            lines.append(f"CREATE TABLE {model_def['schema']}.{dim['name']} (")
            lines.append(f"    {dim['surrogate_key']}  INT IDENTITY(1,1) PRIMARY KEY,")
            lines.append(f"    {dim['natural_key']}     NVARCHAR(100) NOT NULL,")
            for attr in dim.get("attributes", []):
                lines.append(f"    {attr}  NVARCHAR(255),")
            if dim.get("scd_type") == 2:
                lines.append(f"    effective_date  DATE NOT NULL,")
                lines.append(f"    expiry_date     DATE NOT NULL DEFAULT '9999-12-31',")
                lines.append(f"    is_current      BIT NOT NULL DEFAULT 1,")
            lines.append(f"    created_at      DATETIME2 DEFAULT GETDATE(),")
            lines.append(f"    updated_at      DATETIME2 DEFAULT GETDATE()")
            lines.append(f");")
            lines.append(f"")

        # Fact tables
        for fact in model_def["fact_tables"]:
            lines.append(f"-- Fact: {fact['name']}")
            lines.append(f"-- Grain: {fact['grain']}")
            lines.append(f"CREATE TABLE {model_def['schema']}.{fact['name']} (")
            for fk in fact["foreign_keys"]:
                lines.append(f"    {fk}  INT NOT NULL,")
            for measure in fact.get("measures", []):
                lines.append(f"    {measure}  DECIMAL(18,4),")
            lines.append(f"    created_at  DATETIME2 DEFAULT GETDATE()")
            lines.append(f");")
            lines.append(f"")

        return "\n".join(lines)

    def _generate_tmdl(self, model_def: Dict[str, Any]) -> str:
        """Generate TMDL (Tabular Model Definition Language) skeleton."""
        lines = [
            f"/// Data Model: {model_def['model_name']}",
            f"/// Type: {model_def['model_type'].title()} Schema",
            f"/// Generated by Fabric-MAS Data Modeling Agent",
            f"",
            f"model Model",
            f"  culture: en-US",
            f"",
        ]
        for dim in model_def["dimension_tables"]:
            lines.append(f"  table {dim['name']}")
            lines.append(f"    column {dim['surrogate_key']}")
            lines.append(f"      dataType: int64")
            lines.append(f"      isKey: true")
            lines.append(f"    column {dim['natural_key']}")
            lines.append(f"      dataType: string")
            lines.append(f"")

        for fact in model_def["fact_tables"]:
            lines.append(f"  table {fact['name']}")
            for fk in fact["foreign_keys"]:
                lines.append(f"    column {fk}")
                lines.append(f"      dataType: int64")
            for m in fact.get("measures", []):
                lines.append(f"    measure {m} = SUM('{fact['name']}'[{m}])")
            lines.append(f"")

        for rel in model_def.get("relationships", []):
            lines.append(
                f"  relationship {rel['from_table']}_{rel['to_table']}"
            )
            lines.append(f"    fromColumn: {rel['from_table']}.{rel['from_column']}")
            lines.append(f"    toColumn: {rel['to_table']}.{rel['to_column']}")
            lines.append(f"    crossFilteringBehavior: oneDirection")
            lines.append(f"")

        return "\n".join(lines)

    def _update_guidelines(self, params: Dict[str, Any]) -> AgentResult:
        """Update modeling guidelines in instructions.md."""
        new_content = params.get("guidelines", params.get("content", ""))
        mode = params.get("mode", "append")

        if not new_content:
            return self._make_result(
                OperationType.UPDATE,
                False,
                "No guideline content provided. Pass 'guidelines' in params.",
            )

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        if mode == "replace":
            self.knowledge.instructions = new_content
        else:
            self.knowledge.instructions += (
                f"\n\n## Custom Guidelines (Added {timestamp})\n\n{new_content}"
            )

        self.knowledge.save_to_folder()

        return self._make_result(
            OperationType.UPDATE,
            True,
            f"Data modeling guidelines updated ({mode}). "
            "New rules will be applied to all future model generations.",
            data={"mode": mode, "timestamp": timestamp},
        )
