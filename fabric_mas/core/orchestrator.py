"""
orchestrator.py — The Master Brain 🧠 (Copilot-Native Edition)
================================================================
Parses natural-language prompts using intelligent keyword-based routing
and maps them to the correct agents.  No external LLM API required —
GitHub Copilot acts as the LLM via VS Code MCP integration.

Auto-discovers agents from the folder-based layout:
    fabric_mas/agents/<agent-name>/agent.py

Architecture:
    VS Code Copilot (LLM) → calls MCP tools → Orchestrator routes → Agents execute
"""

from __future__ import annotations

import importlib
import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType
from fabric_mas.core.cli_wrapper import FabricCLI
from fabric_mas.tools.search_tool import SearchTool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Plan data structures
# ---------------------------------------------------------------------------
@dataclass
class TaskStep:
    """A single step in an execution plan."""
    step_number: int
    agent_key: str
    operation: str
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    result: Optional[AgentResult] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "agent": self.agent_key,
            "operation": self.operation,
            "params": self.params,
            "description": self.description,
            "result": self.result.to_dict() if self.result else None,
        }


@dataclass
class ExecutionPlan:
    """Ordered list of TaskSteps produced by the planner."""
    prompt: str
    steps: List[TaskStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "steps": [s.to_dict() for s in self.steps],
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Agent Registry — auto-discovers folder-based agents
# ---------------------------------------------------------------------------
class AgentRegistry:
    """
    Central registry that maps item keys / codes to concrete agent classes.
    Auto-discovers agents from fabric_mas/agents/<name>/agent.py.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._aliases: Dict[str, str] = {}

    def register(self, agent_cls: Type[BaseAgent], *aliases: str) -> None:
        key = agent_cls.ITEM_TYPE.lower().replace(" ", "_")
        self._agents[key] = agent_cls
        if agent_cls.ITEM_CODE:
            self._aliases[agent_cls.ITEM_CODE.lower()] = key
        if agent_cls.FAB_NOUN:
            self._aliases[agent_cls.FAB_NOUN.lower()] = key
        if agent_cls.AGENT_FOLDER_NAME:
            self._aliases[agent_cls.AGENT_FOLDER_NAME.lower()] = key
        for alias in aliases:
            self._aliases[alias.lower()] = key
        logger.debug("Registered: %s (%s)", key, agent_cls.ITEM_CODE)

    def get(self, key: str) -> Optional[Type[BaseAgent]]:
        k = key.lower().replace(" ", "_").replace("-", "_")
        if k in self._agents:
            return self._agents[k]
        resolved = self._aliases.get(k)
        if resolved:
            return self._agents.get(resolved)
        # Try partial match
        for alias, agent_key in self._aliases.items():
            if k in alias or alias in k:
                return self._agents.get(agent_key)
        return None

    def list_agents(self) -> List[str]:
        return sorted(self._agents.keys())

    def agent_descriptions(self) -> str:
        """Markdown list for display."""
        lines: List[str] = []
        for key, cls in sorted(self._agents.items()):
            lines.append(f"- **{key}** ({cls.ITEM_CODE}): {cls.ITEM_TYPE}")
        return "\n".join(lines)

    def agent_details(self) -> List[Dict[str, Any]]:
        """Structured agent info for MCP tool responses."""
        details = []
        for key, cls in sorted(self._agents.items()):
            details.append({
                "key": key,
                "item_type": cls.ITEM_TYPE,
                "item_code": cls.ITEM_CODE,
                "fab_noun": cls.FAB_NOUN,
                "folder": cls.AGENT_FOLDER_NAME,
                "operations": ["create", "update", "delete", "analyze", "deploy"],
            })
        return details


# ---------------------------------------------------------------------------
# Keyword-based intelligent planner (no external LLM needed)
# ---------------------------------------------------------------------------

# Operation keyword mapping
OPERATION_KEYWORDS = {
    "create": [
        "create", "build", "make", "set up", "setup", "provision", "add",
        "new", "deploy new", "configure", "initialize", "init", "establish",
        "generate", "scaffold", "spin up",
    ],
    "update": [
        "update", "modify", "change", "edit", "alter", "rename", "patch",
        "reconfigure", "adjust", "set", "assign", "move",
    ],
    "delete": [
        "delete", "remove", "destroy", "drop", "clean up", "cleanup",
        "tear down", "teardown", "purge", "decommission",
    ],
    "analyze": [
        "analyze", "analyse", "list", "show", "get", "describe", "inspect",
        "check", "status", "view", "audit", "monitor", "query", "search",
        "find", "look up", "lookup", "report on", "review", "scan",
    ],
    "deploy": [
        "deploy", "promote", "publish", "release", "push", "migrate",
        "stage", "ship",
    ],
}

# Agent keyword mapping — maps natural language terms to agent keys
AGENT_KEYWORDS: Dict[str, List[str]] = {
    "lakehouse": [
        "lakehouse", "lake house", "delta lake", "bronze", "silver", "gold", "medallion",
    ],
    "onelake": ["onelake", "one lake", "adls", "data lake storage"],
    "shortcut": ["shortcut", "link", "symlink", "pointer"],
    "notebook": ["notebook", "nb", "jupyter", "script", "etl notebook", "pyspark"],
    "environment": ["environment", "env", "runtime", "spark config", "library"],
    "spark_job_definition": ["spark job", "spark definition", "sjd", "batch job"],
    "data_pipeline": [
        "pipeline", "data pipeline", "etl pipeline", "orchestration pipeline",
    ],
    "dataflow_gen2": ["dataflow", "data flow", "dataflow gen2", "power query", "mashup"],
    "copy_job": ["copy job", "copy activity", "data copy", "copy task"],
    "azure_data_factory": ["adf", "azure data factory", "data factory"],
    "warehouse": [
        "warehouse", "data warehouse", "wh", "synapse warehouse", "sql warehouse",
    ],
    "sql_endpoint": ["sql endpoint", "sql analytics", "lakehouse sql"],
    "sql_database": ["sql database", "sql db"],
    "mirrored_database": ["mirrored", "mirror database", "mirrored db", "db mirror"],
    "kql_database": ["kql database", "kql db", "kusto database", "kusto"],
    "eventhouse": ["eventhouse", "event house", "event store"],
    "eventstream": ["eventstream", "event stream", "streaming", "real-time ingest"],
    "kql_queryset": ["kql query", "kql queryset", "kusto query"],
    "real-time_hub": ["realtime hub", "real-time hub", "real time hub"],
    "real-time_dashboard": ["realtime dashboard", "real-time dashboard", "live dashboard"],
    "data_activator": ["data activator", "activator", "trigger", "alert"],
    "reflex": ["reflex", "reactive", "reflex trigger"],
    "semantic_model": [
        "semantic model", "dataset", "tabular model", "power bi model",
    ],
    "report": ["report", "power bi report", "pbi report", "paginated report"],
    "dashboard": ["dashboard", "power bi dashboard", "pbi dashboard"],
    "power_bi_app": ["powerbi app", "power bi app", "pbi app"],
    "organizational_app": ["org app", "organizational app", "template app"],
    "map_visual": ["map visual", "arcgis", "geographic"],
    "workspace": ["workspace", "ws", "project space", "fabric workspace"],
    "capacity": ["capacity", "sku", "compute", "f64", "f32", "f16", "f2"],
    "domain": ["domain", "data domain", "organizational domain"],
    "deployment_pipeline": [
        "deployment pipeline", "deploy pipeline", "ci/cd", "promotion",
    ],
    "git_integration": ["git", "github", "devops", "version control", "source control"],
    "lineage": ["lineage", "data lineage", "impact analysis", "dependency"],
    "sensitivity_label": [
        "sensitivity", "label", "classification", "information protection",
    ],
    "variable_library": ["variable", "variable library", "parameter", "config variable"],
    "task_flow": ["task flow", "taskflow", "dag"],
    "security": [
        "security", "rls", "row level security", "ols", "role", "permission",
        "rbac", "access control",
    ],
    "fabric_iq": ["fabric iq", "ai assistant"],
    "data_agent": ["data agent", "autonomous agent"],
    "copilot": ["copilot settings", "copilot config"],
    "graphql_api": ["graphql", "api endpoint", "graphql api"],
    "user-defined_function": ["udf", "user defined function", "custom function"],
    "ai_functions": ["ai function", "ai functions", "ml function"],
    "ontology": ["ontology", "knowledge graph", "semantic layer"],
    "data_wrangler": ["data wrangler", "wrangler", "data prep", "data preparation"],
    "operations": ["operations", "monitoring", "admin", "ops", "fabric operations"],
    "data_modeling": [
        "data model", "dimension model", "fact table", "dimension table",
        "star schema", "snowflake schema", "scd", "slowly changing",
        "data modeling", "data modelling", "dim model", "kimball",
    ],
}


def _detect_operation(prompt: str) -> str:
    """Detect the operation type from the prompt text."""
    prompt_lower = prompt.lower()
    scores: Dict[str, int] = {op: 0 for op in OPERATION_KEYWORDS}
    for op, keywords in OPERATION_KEYWORDS.items():
        for kw in keywords:
            if kw in prompt_lower:
                scores[op] += len(kw)  # Longer matches score higher
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "analyze"


def _detect_agents(prompt: str, registry: AgentRegistry) -> List[str]:
    """Detect which agents are needed from the prompt text."""
    prompt_lower = prompt.lower()
    matched: List[tuple] = []  # (score, agent_key)

    # Words like "workspace" after a preposition are parameters, not targets.
    # E.g. "Create a Lakehouse in workspace X" → workspace is a parameter.
    _PARAM_CONTEXT = re.compile(
        r"\b(?:in|from|to|into|inside|within|under|on|of)\s+(?:the\s+)?$"
    )

    for agent_key, keywords in AGENT_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw not in prompt_lower:
                continue
            # Check if this keyword is preceded by a preposition (parameter context)
            for m in re.finditer(re.escape(kw), prompt_lower):
                before = prompt_lower[:m.start()]
                if _PARAM_CONTEXT.search(before):
                    # "in workspace X" → parameter, skip this match
                    pass
                else:
                    score += len(kw)
        if score > 0:
            # Verify agent exists in registry
            resolved = registry.get(agent_key)
            if resolved:
                actual_key = resolved.ITEM_TYPE.lower().replace(" ", "_")
                matched.append((score, actual_key))

    # De-duplicate and sort by score (highest first)
    seen = set()
    unique = []
    for score, key in sorted(matched, key=lambda x: -x[0]):
        if key not in seen:
            seen.add(key)
            unique.append(key)

    return unique


def _extract_params(prompt: str) -> Dict[str, Any]:
    """
    Extract parameters from the prompt using pattern matching.

    Handles:
    - Quoted names: "MyItem" or 'MyItem'
    - Workspace IDs: workspace abc-123
    - Item IDs: item abc-123
    - Named patterns: called X, named X
    - Cross-workspace references:
        "from WORKSPACE_A/ITEM_X to WORKSPACE_B/ITEM_Y"
        "from ITEM_X in WORKSPACE_A to ITEM_Y in WORKSPACE_B"
        "copy ITEM_X from WORKSPACE_A to ITEM_Y in WORKSPACE_B"
    """
    params: Dict[str, Any] = {}

    # Extract quoted names
    quoted = re.findall(r'["\']([^"\']+)["\']', prompt)
    if quoted:
        params["display_name"] = quoted[0]
        if len(quoted) > 1:
            params["description"] = quoted[1]

    # Extract workspace ID patterns (GUIDs)
    ws_match = re.search(
        r'(?:workspace|ws)[\s_-]*(?:id)?[\s:=]*([a-f0-9-]{36}|[a-zA-Z0-9_-]+)',
        prompt, re.IGNORECASE,
    )
    if ws_match:
        params["workspace_id"] = ws_match.group(1)

    # Extract item ID patterns
    id_match = re.search(
        r'(?:item|id)[\s:=]*([a-f0-9-]{36})',
        prompt, re.IGNORECASE,
    )
    if id_match:
        params["item_id"] = id_match.group(1)

    # Extract names from natural patterns like "called X" or "named X"
    name_match = re.search(
        r'(?:called|named|name)\s+["\']?([A-Za-z0-9_-]+)["\']?',
        prompt, re.IGNORECASE,
    )
    if name_match and "display_name" not in params:
        params["display_name"] = name_match.group(1)

    # ------------------------------------------------------------------
    # Cross-workspace reference extraction
    # Patterns:
    #   "from WORKSPACE/ITEM to WORKSPACE/ITEM"
    #   "from ITEM in WORKSPACE to ITEM in WORKSPACE"
    #   "copy from WORKSPACE/ITEM to WORKSPACE/ITEM"
    # ------------------------------------------------------------------
    cross_ws_params = _extract_cross_workspace_refs(prompt)
    if cross_ws_params:
        params.update(cross_ws_params)

    return params


def _extract_cross_workspace_refs(prompt: str) -> Dict[str, Any]:
    """
    Extract cross-workspace source/sink references from a prompt.

    Supports patterns like:
    - "from WS_A/LH_X to WS_B/LH_Y"
    - "from LH_X in WS_A to LH_Y in WS_B"
    - "copy from WS_A/LH_X to WS_B/LH_Y"
    - "from LH_MDM_SECURITY to LH_MDM" (same workspace, items only)

    Returns dict with source_workspace, source_item, sink_workspace, sink_item.
    """
    params: Dict[str, Any] = {}

    # Pattern 1: "from WORKSPACE/ITEM to WORKSPACE/ITEM"
    #   e.g. "from DIGITEAM_FAB_SELFSERVICE_PUBLIC/LH_MDM_SECURITY to DIG_FAB_MULTIAGENT/LH_MDM"
    slash_pattern = re.search(
        r'from\s+([A-Za-z0-9_-]+)\s*/\s*([A-Za-z0-9_-]+)\s+'
        r'to\s+([A-Za-z0-9_-]+)\s*/\s*([A-Za-z0-9_-]+)',
        prompt, re.IGNORECASE,
    )
    if slash_pattern:
        params["source_workspace"] = slash_pattern.group(1)
        params["source_item"] = slash_pattern.group(2)
        params["sink_workspace"] = slash_pattern.group(3)
        params["sink_item"] = slash_pattern.group(4)
        return params

    # Pattern 2: "from ITEM in WORKSPACE to ITEM in WORKSPACE"
    #   e.g. "from LH_MDM_SECURITY in DIGITEAM_FAB_SELFSERVICE_PUBLIC to LH_MDM in DIG_FAB_MULTIAGENT"
    in_pattern = re.search(
        r'from\s+([A-Za-z0-9_-]+)\s+in\s+([A-Za-z0-9_-]+)\s+'
        r'to\s+([A-Za-z0-9_-]+)\s+in\s+([A-Za-z0-9_-]+)',
        prompt, re.IGNORECASE,
    )
    if in_pattern:
        params["source_item"] = in_pattern.group(1)
        params["source_workspace"] = in_pattern.group(2)
        params["sink_item"] = in_pattern.group(3)
        params["sink_workspace"] = in_pattern.group(4)
        return params

    # Pattern 3: "from ITEM to ITEM" (same workspace — no workspace specified)
    #   e.g. "from LH_MDM_SECURITY to LH_MDM"
    simple_pattern = re.search(
        r'from\s+([A-Za-z0-9_-]+)\s+to\s+([A-Za-z0-9_-]+)',
        prompt, re.IGNORECASE,
    )
    if simple_pattern:
        src = simple_pattern.group(1)
        sink = simple_pattern.group(2)
        # Filter out common noise words
        noise = {"workspace", "lakehouse", "warehouse", "pipeline", "the", "a", "an"}
        if src.lower() not in noise and sink.lower() not in noise:
            params["source_item"] = src
            params["sink_item"] = sink

    return params


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
class Orchestrator:
    """
    The Master Brain (Copilot-Native).

    Architecture:
        GitHub Copilot (LLM) → MCP Tools → Orchestrator → Agents → Fabric CLI

    The orchestrator uses intelligent keyword-based routing to decompose
    prompts into execution plans. GitHub Copilot handles the natural language
    understanding via MCP tool calls — no external LLM API needed.
    """

    def __init__(
        self,
        *,
        workspace_id: Optional[str] = None,
        cli: Optional[FabricCLI] = None,
        rest_client: Any = None,
        search: Optional[SearchTool] = None,
        registry: Optional[AgentRegistry] = None,
    ):
        self.workspace_id = workspace_id
        self.cli = cli or FabricCLI()
        self.rest_client = rest_client  # FabricRestClient (preferred over CLI)
        self.search = search or SearchTool()
        self.registry = registry or AgentRegistry()
        self._agent_instances: Dict[str, BaseAgent] = {}

    # ------------------------------------------------------------------
    # Auto-discover folder-based agents
    # ------------------------------------------------------------------
    def auto_register(self) -> None:
        """
        Scan fabric_mas/agents/ for sub-folders containing agent.py,
        import each, and register every BaseAgent subclass found.
        """
        agents_root = Path(__file__).resolve().parent.parent / "agents"
        if not agents_root.is_dir():
            logger.error("Agents directory not found: %s", agents_root)
            return

        for child in sorted(agents_root.iterdir()):
            if not child.is_dir() or child.name.startswith("_"):
                continue
            agent_py = child / "agent.py"
            if not agent_py.exists():
                continue
            # Use spec_from_file_location so hyphenated folder names work
            safe_module = f"fabric_mas.agents.{child.name.replace('-', '_')}.agent"
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(safe_module, str(agent_py))
                if spec is None or spec.loader is None:
                    logger.warning("Cannot create spec for %s", agent_py)
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseAgent)
                        and attr is not BaseAgent
                        and attr.ITEM_TYPE
                    ):
                        self.registry.register(attr)
            except Exception as exc:
                logger.warning("Failed to import %s: %s", safe_module, exc)

        logger.info(
            "Auto-registered %d agents: %s",
            len(self.registry.list_agents()),
            ", ".join(self.registry.list_agents()),
        )

    # ------------------------------------------------------------------
    # Planning — keyword-based intelligent routing (no LLM API needed)
    # ------------------------------------------------------------------
    def plan(self, prompt: str) -> ExecutionPlan:
        """
        Produce an execution plan from a prompt using keyword-based routing.

        GitHub Copilot handles the NLU layer via MCP tool descriptions.
        This planner handles the agent routing and parameter extraction.

        Smart planning:
        - If cross-workspace refs are detected (source/sink), automatically
          generates a pipeline creation plan with Copy Activity configuration.
        - Generates auto-names following naming convention if display_name
          is not explicitly provided.
        """
        operation = _detect_operation(prompt)
        agents = _detect_agents(prompt, self.registry)

        if not agents:
            return ExecutionPlan(
                prompt=prompt,
                metadata={
                    "error": "Could not identify target agents from prompt.",
                    "suggestion": "Try mentioning specific Fabric items like "
                                  "'lakehouse', 'notebook', 'pipeline', etc.",
                },
            )

        steps: List[TaskStep] = []
        base_params = _extract_params(prompt)

        # Inject default workspace if not in prompt
        if self.workspace_id and "workspace_id" not in base_params:
            base_params["workspace_id"] = self.workspace_id

        # ------------------------------------------------------------------
        # Smart planning: pipeline with copy activity (cross-workspace)
        # ------------------------------------------------------------------
        has_source_sink = "source_item" in base_params and "sink_item" in base_params
        is_pipeline_op = "data_pipeline" in agents or "datapipeline" in agents

        if has_source_sink and (is_pipeline_op or operation == "create"):
            plan = self._plan_pipeline_with_copy(prompt, base_params, agents, operation)
            if plan:
                return plan

        # ------------------------------------------------------------------
        # Standard planning (single operation per agent)
        # ------------------------------------------------------------------
        for i, agent_key in enumerate(agents, start=1):
            step_params = dict(base_params)
            agent_cls = self.registry.get(agent_key)
            if agent_cls:
                item_name = agent_cls.ITEM_TYPE
            else:
                item_name = agent_key.replace("_", " ").title()

            steps.append(TaskStep(
                step_number=i,
                agent_key=agent_key,
                operation=operation,
                params=step_params,
                description=f"{operation.title()} {item_name}",
            ))

        return ExecutionPlan(
            prompt=prompt,
            steps=steps,
            metadata={
                "planner": "keyword-routing",
                "detected_operation": operation,
                "detected_agents": agents,
            },
        )

    def _plan_pipeline_with_copy(
        self,
        prompt: str,
        params: Dict[str, Any],
        agents: List[str],
        operation: str,
    ) -> Optional[ExecutionPlan]:
        """
        Generate a smart execution plan for creating a pipeline with Copy Activity.

        When the prompt contains cross-workspace source/sink references,
        this method builds a plan that:
        1. Creates the pipeline
        2. Auto-configures the Copy Activity with resolved source/sink

        Auto-generates a pipeline name from source/sink names if not provided.
        """
        source_item = params.get("source_item", "")
        sink_item = params.get("sink_item", "")
        source_workspace = params.get("source_workspace")
        sink_workspace = params.get("sink_workspace")

        # Auto-generate pipeline name if not provided
        display_name = params.get("display_name")
        if not display_name:
            # Generate: PL_COPY_<SOURCE>_TO_<SINK>
            src_short = source_item.replace("LH_", "").replace("WH_", "")
            sink_short = sink_item.replace("LH_", "").replace("WH_", "")
            display_name = f"PL_COPY_{src_short}_TO_{sink_short}"
            params["display_name"] = display_name

        # Build pipeline creation params including source/sink config
        pipeline_params = {
            "display_name": display_name,
            "workspace_id": params.get("workspace_id", self.workspace_id),
            "description": params.get(
                "description",
                f"Copy data from {source_item} to {sink_item}",
            ),
            "source_workspace": source_workspace,
            "source_item": source_item,
            "sink_workspace": sink_workspace,
            "sink_item": sink_item,
            "source_type": params.get("source_type", "Lakehouse"),
            "sink_type": params.get("sink_type", "Lakehouse"),
        }

        steps = [
            TaskStep(
                step_number=1,
                agent_key="datapipeline",
                operation="create",
                params=pipeline_params,
                description=(
                    f"Create pipeline '{display_name}' with Copy Activity: "
                    f"{source_item} → {sink_item}"
                ),
            ),
        ]

        return ExecutionPlan(
            prompt=prompt,
            steps=steps,
            metadata={
                "planner": "smart-pipeline-copy",
                "detected_operation": operation,
                "detected_agents": agents,
                "cross_workspace": True,
                "source": {
                    "item": source_item,
                    "workspace": source_workspace,
                },
                "sink": {
                    "item": sink_item,
                    "workspace": sink_workspace,
                },
            },
        )

    def plan_from_json(self, plan_json: str) -> ExecutionPlan:
        """
        Parse an explicit JSON execution plan (e.g. from Copilot).

        When Copilot directly provides a structured plan via the MCP tool,
        this method parses it into an ExecutionPlan without keyword detection.
        """
        try:
            data = json.loads(plan_json)
        except json.JSONDecodeError as exc:
            return ExecutionPlan(
                prompt=plan_json,
                metadata={"error": f"JSON parse error: {exc}"},
            )

        steps: List[TaskStep] = []
        for i, sd in enumerate(data.get("steps", []), start=1):
            steps.append(TaskStep(
                step_number=i,
                agent_key=sd.get("agent_key", ""),
                operation=sd.get("operation", ""),
                params=sd.get("params", {}),
                description=sd.get("description", ""),
            ))
        return ExecutionPlan(
            prompt=data.get("prompt", ""),
            steps=steps,
            metadata=data.get("metadata", {"planner": "copilot-direct"}),
        )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def _get_agent_instance(self, key: str) -> Optional[BaseAgent]:
        if key in self._agent_instances:
            return self._agent_instances[key]
        agent_cls = self.registry.get(key)
        if agent_cls is None:
            return None
        agent = agent_cls(
            workspace_id=self.workspace_id,
            cli=self.cli,
            rest_client=self.rest_client,
            search=self.search,
        )
        self._agent_instances[key] = agent
        return agent

    def execute_plan(self, plan: ExecutionPlan) -> List[AgentResult]:
        results: List[AgentResult] = []
        for step in plan.steps:
            logger.info(
                "▶ Step %d: %s.%s — %s",
                step.step_number, step.agent_key, step.operation, step.description,
            )
            agent = self._get_agent_instance(step.agent_key)
            if agent is None:
                result = AgentResult(
                    success=False,
                    operation=step.operation,
                    agent_name="orchestrator",
                    item_type=step.agent_key,
                    message=f"No agent registered for '{step.agent_key}'",
                )
            else:
                result = agent.execute(step.operation, step.params)
                # ── Auto-learning: log prompt → agent's examples.md ──
                try:
                    agent.knowledge.log_prompt(
                        prompt=plan.prompt,
                        operation=step.operation,
                        result_summary=result.message,
                        success=result.success,
                    )
                except Exception as exc:
                    logger.warning("Prompt logging failed for %s: %s", step.agent_key, exc)
            step.result = result
            results.append(result)
            logger.info("  %s", result)
        return results

    # ------------------------------------------------------------------
    # Direct agent execution (called by granular MCP tools)
    # ------------------------------------------------------------------
    def execute_agent_directly(
        self,
        agent_key: str,
        operation: str,
        params: Dict[str, Any],
    ) -> AgentResult:
        """
        Execute a single agent operation directly, bypassing the planner.
        Used by granular MCP tools that Copilot calls with specific intent.
        """
        agent = self._get_agent_instance(agent_key)
        if agent is None:
            return AgentResult(
                success=False,
                operation=operation,
                agent_name="orchestrator",
                item_type=agent_key,
                message=f"No agent registered for '{agent_key}'",
            )

        # Inject workspace_id if not provided
        if self.workspace_id and "workspace_id" not in params:
            params["workspace_id"] = self.workspace_id

        result = agent.execute(operation, params)

        # Auto-learning
        try:
            agent.knowledge.log_prompt(
                prompt=f"[Direct] {operation} {agent_key} with {json.dumps(params)}",
                operation=operation,
                result_summary=result.message,
                success=result.success,
            )
        except Exception as exc:
            logger.warning("Prompt logging failed for %s: %s", agent_key, exc)

        return result

    # ------------------------------------------------------------------
    # Main entry point — called from MCP
    # ------------------------------------------------------------------
    def execute_task(self, prompt: str) -> Dict[str, Any]:
        """End-to-end: prompt → plan → execute → structured result."""
        logger.info("═══ New task ═══\n%s", prompt)

        # Check if prompt is a JSON plan from Copilot
        stripped = prompt.strip()
        if stripped.startswith("{") and '"steps"' in stripped:
            plan = self.plan_from_json(stripped)
        else:
            plan = self.plan(stripped)

        if not plan.steps:
            return {
                "success": False,
                "message": "Could not produce an execution plan. "
                           + plan.metadata.get("suggestion", ""),
                "plan": plan.to_dict(),
                "results": [],
            }
        results = self.execute_plan(plan)
        all_ok = all(r.success for r in results)

        # ── Auto-learning: log the overall task to orchestrator's own memory ──
        self._log_orchestrator_prompt(prompt, plan, results, all_ok)

        # ── Visual workflow: render terminal + export HTML ──
        html_path = None
        try:
            from fabric_mas.tools.workflow_visualizer import visualize_execution
            html_path = visualize_execution(plan, results, export_html=True)
        except Exception as exc:
            logger.debug("Workflow visualizer skipped: %s", exc)

        return {
            "success": all_ok,
            "message": (
                f"Executed {len(results)} step(s) — "
                + ("all succeeded ✅" if all_ok else "some steps failed ❌")
            ),
            "plan": plan.to_dict(),
            "results": [r.to_dict() for r in results],
            "workflow_html": html_path,
        }

    # ------------------------------------------------------------------
    # Orchestrator-level prompt logging (writes to orchestrator-agent/)
    # ------------------------------------------------------------------
    def _log_orchestrator_prompt(
        self,
        prompt: str,
        plan: ExecutionPlan,
        results: List[AgentResult],
        all_ok: bool,
    ) -> None:
        """Append execution summary to orchestrator-agent/examples.md."""
        from datetime import datetime, timezone

        orchestrator_dir = (
            Path(__file__).resolve().parent.parent / "agents" / "orchestrator-agent"
        )
        ex_path = orchestrator_dir / "examples.md"
        if not orchestrator_dir.is_dir():
            logger.debug("orchestrator-agent/ folder not found — skipping prompt log")
            return

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        status = "✅ All Succeeded" if all_ok else "❌ Partial Failure"
        agents_used = ", ".join(s.agent_key for s in plan.steps)
        entry = (
            f"\n### {timestamp} — ORCHESTRATION [{status}]\n"
            f"**Prompt:** {prompt}\n\n"
            f"**Agents Used:** {agents_used}\n\n"
            f"**Steps:** {len(plan.steps)} | "
            f"**Succeeded:** {sum(1 for r in results if r.success)} | "
            f"**Failed:** {sum(1 for r in results if not r.success)}\n\n"
            f"---\n"
        )
        try:
            with open(ex_path, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as exc:
            logger.warning("Failed to log orchestrator prompt: %s", exc)
