"""
mcp_server.py — FastMCP Entry Point for VS Code (Copilot-Native)
==================================================================
Exposes the Fabric-MAS system as MCP tools that GitHub Copilot in VS Code
can invoke directly.  No OpenAI API key required — Copilot IS the LLM.

Run with:
    python mcp_server.py            # stdio transport (VS Code default)
    python mcp_server.py --sse      # SSE transport (HTTP)

Architecture:
    GitHub Copilot (LLM) → VS Code MCP → This Server → Orchestrator → Agents → Fabric CLI
"""

from __future__ import annotations

import json
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("fabric-mas-mcp")

# ---------------------------------------------------------------------------
# FastMCP setup
# ---------------------------------------------------------------------------
from fastmcp import FastMCP

mcp = FastMCP(
    "Fabric-MAS",
    instructions=(
        "Multi-Agent System for managing Microsoft Fabric resources via natural language. "
        "49 dedicated agents — one per Fabric item type + data modeling — orchestrated "
        "by a Master Brain. Powered by GitHub Copilot (no OpenAI API key needed). "
        "Use these tools to create, update, delete, analyze, and deploy any Fabric resource."
    ),
)

# ---------------------------------------------------------------------------
# Lazy-init orchestrator (no OpenAI key required)
# ---------------------------------------------------------------------------
_orchestrator = None


def _get_orchestrator():
    global _orchestrator
    if _orchestrator is not None:
        return _orchestrator

    from fabric_mas.core.orchestrator import Orchestrator
    from fabric_mas.core.cli_wrapper import FabricCLI
    from fabric_mas.tools.search_tool import SearchTool

    cli = FabricCLI(
        default_workspace_id=os.getenv("FABRIC_WORKSPACE_ID"),
        dry_run=os.getenv("FABRIC_DRY_RUN", "false").lower() == "true",
    )
    search = SearchTool()

    orch = Orchestrator(
        workspace_id=os.getenv("FABRIC_WORKSPACE_ID"),
        cli=cli,
        search=search,
    )
    orch.auto_register()
    _orchestrator = orch
    logger.info(
        "Orchestrator ready — %d agents registered (Copilot-native, no API key needed)",
        len(orch.registry.list_agents()),
    )
    return orch


# ---------------------------------------------------------------------------
# MCP Tools — Rich descriptions help Copilot route correctly
# ---------------------------------------------------------------------------


@mcp.tool()
def execute_fabric_task(prompt: str) -> str:
    """
    Execute a Microsoft Fabric management task from a natural-language prompt.

    The Master Brain parses the prompt, identifies the correct agents, and
    orchestrates CLI/API operations. Supports multi-step workflows.

    Examples:
        - "Create a Medallion architecture with Bronze, Silver, Gold lakehouses
           in workspace abc-123"
        - "List all notebooks in workspace xyz"
        - "Set up an Eventhouse with KQL databases for IoT analytics"
        - "Delete the old staging warehouse"

    You can also pass a JSON execution plan directly:
        {"steps": [{"agent_key": "lakehouse", "operation": "create",
          "params": {"display_name": "Bronze"}, "description": "..."}]}

    Args:
        prompt: Natural-language task description OR a JSON execution plan.

    Returns:
        JSON string with the execution plan, agent results, and workflow HTML path.
    """
    orch = _get_orchestrator()
    result = orch.execute_task(prompt)
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def run_fabric_agent(
    agent_key: str,
    operation: str,
    params: str = "{}",
) -> str:
    """
    Run a specific Fabric agent directly with an explicit operation and parameters.
    Use this when you know exactly which agent and operation to invoke.

    Args:
        agent_key: The agent to invoke (e.g. "lakehouse", "notebook", "workspace",
                   "data_pipeline", "semantic_model", "security", "data_modeling").
        operation: One of: "create", "update", "delete", "analyze", "deploy".
        params:    JSON string of parameters. Common params:
                   - display_name: Name of the item to create/update
                   - workspace_id: Target workspace GUID
                   - item_id: ID of existing item (for update/delete)
                   - description: Item description

    Returns:
        JSON string with the agent execution result.
    """
    orch = _get_orchestrator()
    try:
        parsed_params = json.loads(params) if isinstance(params, str) else params
    except json.JSONDecodeError:
        parsed_params = {}

    result = orch.execute_agent_directly(agent_key, operation, parsed_params)
    return json.dumps(result.to_dict(), indent=2, default=str)


@mcp.tool()
def list_available_agents() -> str:
    """
    List all registered Fabric item agents and their capabilities.
    Use this to discover which agents are available for executing tasks.

    Returns:
        JSON with agent names, item codes, categories, and supported operations.
    """
    orch = _get_orchestrator()
    details = orch.registry.agent_details()
    return json.dumps({"agents": details, "count": len(details)}, indent=2)


@mcp.tool()
def search_fabric_docs(item_type: str, operation: str = "overview") -> str:
    """
    Search for the latest Microsoft Fabric documentation / API reference.

    Args:
        item_type:  Fabric item (e.g. "Lakehouse", "Notebook", "KQLDatabase").
        operation:  Operation to look up (e.g. "create", "REST API").

    Returns:
        JSON with search results from Tavily / Bing.
    """
    orch = _get_orchestrator()
    results = orch.search.search_fabric_api(item_type, operation)
    return json.dumps(results, indent=2, default=str)


@mcp.tool()
def get_agent_knowledge(agent_key: str) -> str:
    """
    Retrieve the knowledge files (instructions, examples,
    known issues) for a specific agent. Useful for understanding
    an agent's capabilities and past execution patterns.

    Args:
        agent_key: Agent key (e.g. "lakehouse", "notebook", "security",
                   "data_modeling", "workspace").

    Returns:
        The combined knowledge context as a formatted string.
    """
    orch = _get_orchestrator()
    agent = orch._get_agent_instance(agent_key)
    if agent is None:
        return json.dumps({"error": f"Agent '{agent_key}' not found"})
    return agent.knowledge.to_context_string()


@mcp.tool()
def update_agent_knowledge(
    agent_key: str,
    file_name: str,
    content: str,
    mode: str = "append",
) -> str:
    """
    Update an agent's knowledge files (instructions, examples, or known_issues).
    Use this to add custom guidelines, examples, or document issues.

    Args:
        agent_key: Agent key (e.g. "data_modeling", "lakehouse", "security").
        file_name: Which file to update: "instructions", "examples", or "known_issues".
        content:   The content to add or replace.
        mode:      "append" to add to existing content, "replace" to overwrite entirely.

    Returns:
        JSON confirmation of the update.
    """
    orch = _get_orchestrator()
    agent = orch._get_agent_instance(agent_key)
    if agent is None:
        return json.dumps({"error": f"Agent '{agent_key}' not found"})

    attr_map = {
        "instructions": "instructions",
        "instructions.md": "instructions",
        "examples": "examples",
        "examples.md": "examples",
        "known_issues": "known_issues",
        "known_issues.md": "known_issues",
    }
    attr = attr_map.get(file_name)
    if attr is None:
        return json.dumps({
            "error": f"Invalid file_name '{file_name}'. "
                     f"Use: instructions, examples, or known_issues"
        })

    if mode == "replace":
        setattr(agent.knowledge, attr, content)
    else:
        current = getattr(agent.knowledge, attr, "")
        setattr(agent.knowledge, attr, current + "\n\n" + content)

    agent.knowledge.save_to_folder()
    return json.dumps({
        "success": True,
        "message": f"Updated {file_name} for {agent_key} agent (mode={mode})",
        "agent": agent_key,
        "file": file_name,
    })


@mcp.tool()
def visualize_workflow(prompt: str) -> str:
    """
    Generate a visual agent workflow diagram for a Fabric task WITHOUT executing it.

    Shows which agents would be activated, in what order, and the data flow.
    Produces both a terminal-rendered view and an HTML file.

    Args:
        prompt: Natural-language description of the Fabric task to visualise.

    Returns:
        JSON with the plan details and path to the generated HTML workflow file.
    """
    orch = _get_orchestrator()
    plan = orch.plan(prompt)
    if not plan.steps:
        return json.dumps({
            "success": False,
            "message": "Could not produce an execution plan to visualise.",
        })

    from fabric_mas.tools.workflow_visualizer import WorkflowVisualizer
    viz = WorkflowVisualizer()
    viz.render_plan(plan, results=None)
    html_path = viz.export_html(plan, results=None)

    return json.dumps({
        "success": True,
        "message": f"Workflow visualised: {len(plan.steps)} steps across "
                   f"{len(set(s.agent_key for s in plan.steps))} agents",
        "plan": plan.to_dict(),
        "workflow_html": html_path,
        "agents_involved": list(set(s.agent_key for s in plan.steps)),
    }, indent=2, default=str)


@mcp.tool()
def get_system_status() -> str:
    """
    Get the current status of the Fabric-MAS system including
    registered agents, configuration, and health.

    Returns:
        JSON with system status, agent count, configuration, and environment info.
    """
    orch = _get_orchestrator()
    return json.dumps({
        "status": "ready",
        "llm_backend": "github-copilot-via-mcp",
        "agents_registered": len(orch.registry.list_agents()),
        "agent_list": orch.registry.list_agents(),
        "workspace_id": orch.workspace_id or "(not set — pass workspace_id in params)",
        "dry_run": orch.cli.dry_run if hasattr(orch.cli, 'dry_run') else False,
        "search_backends": {
            "tavily": bool(orch.search.tavily_api_key),
            "bing": bool(orch.search.bing_api_key),
        },
        "tools_available": [
            "execute_fabric_task",
            "run_fabric_agent",
            "list_available_agents",
            "search_fabric_docs",
            "get_agent_knowledge",
            "update_agent_knowledge",
            "visualize_workflow",
            "get_system_status",
        ],
    }, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    transport = "stdio"
    if "--sse" in sys.argv:
        transport = "sse"
    logger.info("Starting Fabric-MAS MCP server (transport=%s) — Copilot-native, no API key needed", transport)
    mcp.run(transport=transport)
