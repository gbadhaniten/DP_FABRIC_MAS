# 🏗️ ARCHITECTURE — Fabric Multi-Agent System (Fabric-MAS)

> **Copilot-Native** — No OpenAI API key required. GitHub Copilot is the LLM.

## System Overview

Fabric-MAS is a **Python-based multi-agent system** that manages Microsoft Fabric resources
through natural language. It exposes a **Model Context Protocol (MCP)** server that VS Code
GitHub Copilot invokes directly. A keyword-based orchestrator routes user prompts to
**49 specialised agents** — one per Fabric item type + a data modeling agent.

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Copilot (LLM)                         │
│              Your Copilot licence — no API key needed            │
│              Natural language understanding built-in             │
└────────────────────────────┬────────────────────────────────────┘
                             │  MCP Protocol (stdio)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       mcp_server.py                             │
│             FastMCP Server — 8 Exposed Tools                    │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │execute_fabric│ │run_fabric    │ │list_available│            │
│  │    _task     │ │   _agent     │ │   _agents    │            │
│  └──────┬───────┘ └──────┬───────┘ └──────────────┘            │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │search_fabric │ │get_agent     │ │update_agent  │            │
│  │    _docs     │ │ _knowledge   │ │ _knowledge   │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                  │
│  ┌──────────────┐ ┌──────────────┐                              │
│  │visualize     │ │get_system    │                              │
│  │  _workflow   │ │   _status    │                              │
│  └──────────────┘ └──────────────┘                              │
└─────────┬───────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Orchestrator 🧠                                │
│               (Keyword-Based Intelligent Routing)                 │
│                                                                   │
│  ┌────────────────────┐  ┌────────────────────┐                  │
│  │ Keyword Planner    │  │ AgentRegistry      │                  │
│  │ Prompt → detect    │  │ Auto-Discovery     │                  │
│  │ agents + operation │  │ 49 agents scanned  │                  │
│  └────────┬───────────┘  └────────┬───────────┘                  │
│           │                       │                               │
│  ┌────────▼───────────────────────▼───────────┐                  │
│  │         Execution Engine                    │                  │
│  │  plan → execute → auto-learn → visualize   │                  │
│  └────────┬───────────────────────────────────┘                  │
└───────────┼──────────────────────────────────────────────────────┘
            │ Dispatches to agents
            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Agent Layer (49 Agents)                        │
│                                                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐│
│  │ lakehouse-  │ │ notebook-   │ │ pipeline-   │ │data-model- ││
│  │ agent/      │ │ agent/      │ │ agent/      │ │ing-agent/  ││
│  │ ├─agent.py  │ │ ├─agent.py  │ │ ├─agent.py  │ │├─agent.py  ││
│  │ ├─instruct… │ │ ├─instruct… │ │ ├─instruct… │ │├─instruct… ││
│  │ ├─examples  │ │ ├─examples  │ │ ├─examples  │ │├─examples  ││
│  │ └─known_i…  │ │ └─known_i…  │ │ └─known_i…  │ │└─known_i…  ││
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────┬──────┘│
└─────────┼───────────────┼───────────────┼───────────────┼───────┘
          │               │               │               │
          ▼               ▼               ▼               ▼
┌──────────────────────────────────────────────────────────────────┐
│                        FabricCLI Wrapper                         │
│              subprocess → `fab <noun> <verb> ...`                │
│           dry-run · retry · timeout · JSON parsing               │
└──────────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Microsoft Fabric Platform                       │
│        REST APIs · CLI · Workspaces · Capacities · Items         │
└──────────────────────────────────────────────────────────────────┘
```

---

## Key Architecture Decision: Copilot IS the LLM

Previous versions used OpenAI GPT-4o as an internal LLM planner. The current architecture
eliminates this dependency:

| Aspect | Old (OpenAI) | New (Copilot-Native) |
|--------|-------------|---------------------|
| LLM | GPT-4o via API | GitHub Copilot via VS Code |
| API Key | `OPENAI_API_KEY` required | No API key needed |
| Planning | LLM parses prompt → JSON plan | Keyword routing + Copilot NLU |
| Cost | Per-token OpenAI billing | Included in Copilot licence |
| Dependencies | langchain-openai, openai | None (removed) |
| Architecture | MCP → Orchestrator → LLM → Plan → Execute | Copilot → MCP → Route → Execute |

**Why this works:** Copilot already understands natural language. It reads the MCP tool
descriptions, understands the user's intent, and calls the right tool with the right
parameters. The keyword planner in the orchestrator provides fallback routing for
`execute_fabric_task`, while `run_fabric_agent` lets Copilot bypass the planner entirely.

---

## Component Breakdown

### 1. MCP Server (`mcp_server.py`)

| Tool | Purpose |
|------|---------|
| `execute_fabric_task` | Main entry — natural language prompt → plan → execute |
| `run_fabric_agent` | Direct agent call — agent_key + operation + params |
| `list_available_agents` | Discovery — returns all 49 agents |
| `search_fabric_docs` | Search Fabric API/CLI documentation |
| `get_agent_knowledge` | Read an agent's knowledge files |
| `update_agent_knowledge` | Update agent instructions/examples/issues |
| `visualize_workflow` | Preview workflow without executing |
| `get_system_status` | System health and configuration |

### 2. Orchestrator (`fabric_mas/core/orchestrator.py`)

The **Master Brain** — now without LLM dependency:
- **Keyword Planner**: Detects agents and operations from prompt text using weighted keyword matching
- **JSON Plan Parser**: Accepts structured plans directly from Copilot
- **AgentRegistry**: Auto-discovers agents by scanning `agents/*/agent.py`
- **Direct Execution**: `execute_agent_directly()` for granular MCP tool calls
- **Execution Engine**: Iterates plan steps, dispatches to agents, logs results
- **Auto-Learning**: Logs to both agent and orchestrator `examples.md`

### 3. Base Agent (`fabric_mas/core/base_agent.py`)

Abstract base class providing:
- **5 Canonical Operations**: `create`, `update`, `delete`, `analyze`, `deploy`
- **AgentKnowledge**: Auto-loads `.md` files from the agent's folder
- **Auto-Train**: Fetches latest API specs via SearchTool
- **Prompt Memory**: `log_prompt()` auto-appends results to `examples.md`
- **CLI Helper**: Builds and runs `fab` commands via `FabricCLI`

### 4. Agent Knowledge System

| File | Purpose | Update Mode |
|------|---------|-------------|
| `instructions.md` | Agent behaviour rules, API references | Manual / MCP tool |
| `examples.md` | Few-shot examples + auto-logged history | **Manual + Auto** |
| `known_issues.md` | Bugs, workarounds, gotchas | Manual / MCP tool |

### 5. Data Modeling Agent (New)

Specialized agent for dimensional modeling:
- Generates star/snowflake schema models
- Applies SCD Type 1, 2, 3
- Outputs SQL DDL, TMDL, or JSON
- **Updateable guidelines** via `update_agent_knowledge` MCP tool
- Does not execute CLI commands — generates artifacts

---

## Agent Categories (49 Total)

| Category | Count | Agents |
|----------|-------|--------|
| **Data Engineering** | 6 | onelake, lakehouse, shortcut, notebook, environment, spark-job |
| **Data Integration** | 4 | data-pipeline, dataflow, copy-job, adf |
| **Analytics & Warehousing** | 4 | warehouse, sql-endpoint, sql-database, mirrored-db |
| **Real-Time Intelligence** | 8 | kql-database, eventhouse, eventstream, kql-queryset, realtime-hub, realtime-dashboard, data-activator, reflex |
| **Reporting & Power BI** | 6 | semantic-model, report, dashboard, powerbi-app, org-app, map-visual |
| **Governance & Admin** | 10 | workspace, capacity, domain, deployment-pipeline, git-integration, lineage, sensitivity-label, variable-library, task-flow, security |
| **AI & Advanced** | 9 | fabric-iq, data-agent, copilot, graphql-api, udf, ai-functions, ontology, data-wrangler, operations |
| **Data Modeling** | 1 | data-modeling (star/snowflake schema, SCD, naming conventions) |
| **Meta** | 1 | orchestrator (Master Brain) |

---

## Data Flow

```
User types in Copilot Chat:
"Create Bronze lakehouse and ETL notebook in workspace ws-123"
    │
    ▼
┌─ GitHub Copilot ──────────────────────────────┐
│  Reads MCP tool descriptions                   │
│  Decides: call execute_fabric_task             │
│  Passes prompt as argument                     │
└───────────────┬───────────────────────────────┘
                │
                ▼
┌─ Orchestrator.plan() ─────────────────────────┐
│  Keyword detection:                            │
│  • "lakehouse" → lakehouse agent               │
│  • "notebook" → notebook agent                 │
│  • "create" → create operation                 │
│  • "ws-123" → workspace_id parameter           │
│                                                │
│  Plan: [lakehouse.create, notebook.create]     │
└───────────────┬───────────────────────────────┘
                │
                ▼
┌─ Orchestrator.execute_plan() ─────────────────┐
│  Step 1: LakehouseAgent.create(params)         │
│    → fab lakehouse create --display-name Bronze│
│    → log_prompt() → examples.md                │
│                                                │
│  Step 2: NotebookAgent.create(params)          │
│    → fab notebook create --display-name ETL    │
│    → log_prompt() → examples.md                │
└───────────────┬───────────────────────────────┘
                │
                ▼
┌─ Response back to Copilot ────────────────────┐
│  { success: true,                              │
│    message: "Executed 2 steps — all succeeded",│
│    plan: {...}, results: [{...}, {...}] }      │
└────────────────────────────────────────────────┘
```

---

## Auto-Learning Architecture

```
            Execution happens
                    │
            ┌───────┼───────┐
            ▼       ▼       ▼
    Agent A's   Agent B's  Orchestrator's
    examples.md examples.md examples.md
            │       │       │
            └───────┼───────┘
                    │
              Loaded at next
              startup into
              AgentKnowledge
                    │
                    ▼
              Keyword planner
              gets richer context
              for future routing
```

---

## File Structure

```
FABRIC-MAS/
├── mcp_server.py              # FastMCP server — 8 tools
├── setup_wizard.py            # One-prompt setup script
├── requirements.txt           # Dependencies (no OpenAI!)
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── ARCHITECTURE.md            # This file
├── HOW_TO_USE.md              # Setup & usage guide
├── SAMPLE_PROMPTS.md          # Prompt catalogue
├── MASTER_PROMPT.md           # Regeneration prompt
├── GITHUB_DEPLOYMENT.md       # GitHub deployment guide
│
├── .vscode/
│   └── mcp.json               # MCP server configuration
│
├── fabric_mas/
│   ├── core/
│   │   ├── base_agent.py      # BaseAgent ABC + AgentKnowledge
│   │   ├── orchestrator.py    # Keyword planner + AgentRegistry
│   │   └── cli_wrapper.py     # FabricCLI subprocess wrapper
│   │
│   ├── tools/
│   │   ├── search_tool.py     # Tavily/Bing auto-train search
│   │   └── workflow_visualizer.py  # Rich + HTML workflow renderer
│   │
│   └── agents/                # 49 agent folders
│       ├── lakehouse-agent/
│       ├── data-modeling-agent/  # NEW: Dimensional modeling
│       ├── orchestrator-agent/
│       └── ... (49 total)
│
└── workflow_output/           # Auto-generated HTML workflows
```
