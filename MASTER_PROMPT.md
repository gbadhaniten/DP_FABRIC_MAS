# 🔄 MASTER PROMPT — Regenerate Fabric-MAS from Scratch

> **Purpose:** This file is a comprehensive prompt that can be given to an AI assistant
> (Copilot, Claude, GPT, etc.) to regenerate the entire Fabric Multi-Agent System.

---

## Prompt Starts Here

Build a **Fabric Multi-Agent System (Fabric-MAS)** in Python that manages all Microsoft Fabric resources through natural language using VS Code MCP integration. **Copilot-Native: No OpenAI API key required.** Follow these exact specifications:

---

### 1. PROJECT STRUCTURE

```
FABRIC-MAS/
├── mcp_server.py                  # FastMCP server — 8 MCP tools
├── setup_wizard.py                # One-prompt setup script
├── requirements.txt               # Dependencies (NO OpenAI/LangChain)
├── .env.example                   # Environment template (no API keys required)
├── .gitignore                     # Git ignore rules
├── .vscode/mcp.json               # MCP server configuration for VS Code
├── ARCHITECTURE.md                # System architecture documentation
├── HOW_TO_USE.md                  # Setup & usage guide
├── SAMPLE_PROMPTS.md              # Prompt catalogue
├── MASTER_PROMPT.md               # This regeneration prompt
├── GITHUB_DEPLOYMENT.md           # GitHub deployment guide
│
├── fabric_mas/
│   ├── __init__.py
│   ├── core/
│   │   ├── base_agent.py          # BaseAgent ABC + AgentKnowledge
│   │   ├── orchestrator.py        # Keyword planner + AgentRegistry (NO LLM API)
│   │   └── cli_wrapper.py         # FabricCLI subprocess wrapper
│   ├── tools/
│   │   ├── search_tool.py         # Tavily/Bing auto-train search
│   │   └── workflow_visualizer.py # Rich + HTML workflow renderer
│   └── agents/                    # 49 agent folders (one per Fabric item)
│       ├── orchestrator-agent/
│       ├── data-modeling-agent/   # Dimensional modeling specialist
│       ├── lakehouse-agent/
│       └── ... (49 total)
```

---

### 2. KEY DESIGN PRINCIPLES

1. **Copilot IS the LLM** — No OpenAI/LangChain. Copilot calls MCP tools directly.
2. **One Item = One Agent = One Folder** — code + knowledge co-located
3. **8 MCP Tools** — rich descriptions help Copilot route correctly
4. **Keyword-Based Routing** — fallback planner for `execute_fabric_task`
5. **Direct Agent Execution** — `run_fabric_agent` bypasses planner
6. **Auto-Learning** — every execution logged to `examples.md`
7. **Updateable Knowledge** — `update_agent_knowledge` tool for live customization
8. **Auto-Discovery** — orchestrator scans `agents/*/agent.py`
9. **Dry-Run Safe** — all CLI commands support dry-run mode
10. **One-Prompt Setup** — `setup_wizard.py` configures everything

---

### 3. CORE COMPONENTS

#### 3a. `orchestrator.py` — Keyword-Based Planner (NO LLM API)
- `OPERATION_KEYWORDS` dict: maps operations to keyword lists
- `AGENT_KEYWORDS` dict: maps agent keys to keyword lists
- `_detect_operation(prompt)`: weighted keyword scoring
- `_detect_agents(prompt, registry)`: keyword matching with registry validation
- `_extract_params(prompt)`: regex extraction of names, workspace IDs, item IDs
- `Orchestrator.__init__()`: NO `openai_api_key` parameter
- `plan(prompt)`: keyword-based routing, no LLM call
- `plan_from_json(plan_json)`: parses explicit JSON plans from Copilot
- `execute_agent_directly(agent_key, operation, params)`: direct agent call
- `execute_task(prompt)`: end-to-end with auto-learning + visualization

#### 3b. `mcp_server.py` — 8 MCP Tools
1. `execute_fabric_task(prompt)` — natural language → plan → execute
2. `run_fabric_agent(agent_key, operation, params)` — direct agent call
3. `list_available_agents()` — discover all 49 agents
4. `search_fabric_docs(item_type, operation)` — search API docs
5. `get_agent_knowledge(agent_key)` — read agent knowledge
6. `update_agent_knowledge(agent_key, file_name, content, mode)` — update knowledge
7. `visualize_workflow(prompt)` — preview without executing
8. `get_system_status()` — system health check

#### 3c. `base_agent.py` — Same as before (AgentKnowledge + BaseAgent ABC)

#### 3d. `setup_wizard.py` — One-Prompt Setup
7 steps: Python check → venv → deps → .env → Fabric CLI → MCP config → validate

---

### 4. ALL 49 AGENT FOLDERS

Same 48 agents as before PLUS:

| Folder | Class | ITEM_TYPE | ITEM_CODE | FAB_NOUN |
|--------|-------|-----------|-----------|----------|
| `data-modeling-agent` | DataModelingAgent | Data Modeling | DM | (none) |

The Data Modeling Agent:
- Generates star/snowflake schema models
- Applies SCD Type 1, 2, 3
- Outputs SQL DDL, TMDL, or JSON
- Has updateable guidelines in `instructions.md`
- Contains Kimball methodology reference

---

### 5. DEPENDENCIES (`requirements.txt`)
```
# NO OpenAI or LangChain!
mcp>=1.0.0
fastmcp>=0.5.0
tavily-python>=0.3.0
requests>=2.31.0
ms-fabric-cli>=0.1.0
python-dotenv>=1.0.0
pydantic>=2.5.0
rich>=13.7.0
```

---

### 6. `.env.example`
```env
# No OpenAI API key needed! GitHub Copilot is the LLM.
TAVILY_API_KEY=
BING_SEARCH_API_KEY=
FABRIC_WORKSPACE_ID=
FABRIC_DRY_RUN=true
```

---

### 7. `.vscode/mcp.json`
```json
{
  "servers": {
    "fabric-mas": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "."
    }
  }
}
```

---

**Generate all files with complete, production-ready content. Every agent folder must have all 4 files with real, contextual content — not placeholders. No OpenAI/LangChain dependencies.**
