# 📖 HOW TO USE — Fabric Multi-Agent System (Fabric-MAS)

> **Copilot-Native** — No OpenAI API key needed. GitHub Copilot is the LLM.

## Table of Contents
1. [Team Onboarding (New User Setup)](#team-onboarding-new-user-setup)
2. [Do I Need a Prefix or Special Command?](#do-i-need-a-prefix-or-special-command)
3. [Quick Start (One-Prompt Setup)](#quick-start-one-prompt-setup)
4. [Prerequisites](#prerequisites)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [VS Code + Copilot Integration](#vs-code--copilot-integration)
8. [Agent Activation & Lifecycle](#agent-activation--lifecycle)
9. [Using the 8 MCP Tools](#using-the-8-mcp-tools)
10. [Example Sessions](#example-sessions)
11. [Data Modeling Agent](#data-modeling-agent)
12. [Agent Knowledge System](#agent-knowledge-system)
13. [Customising Agents](#customising-agents)
14. [Troubleshooting](#troubleshooting)

---

## Team Onboarding (New User Setup)

> **For anyone joining the project — follow these steps to activate Fabric-MAS in your VS Code.**

### Step 1: Clone the Repository
```powershell
git clone https://github.com/gbadhaniten/DP_FABRIC_MAS.git
cd DP_FABRIC_MAS
git checkout feature/mas/dev_v1
```

### Step 2: Run the One-Prompt Setup Wizard
```powershell
python setup_wizard.py
```
This creates the virtual environment, installs dependencies, generates `.env`, and configures MCP — all in one go.

### Step 3: Authenticate with Microsoft Fabric
```powershell
.venv\Scripts\Activate.ps1
pip install ms-fabric-cli
fab auth login
```
Sign in with your **_AZR** (Azure/Fabric) account when the browser opens.

### Step 4: Open in VS Code & Verify MCP
```powershell
code .
```
Then inside VS Code:
1. Press `Ctrl+Shift+P` → type **MCP: List Servers**
2. You should see **`fabric-mas`** with **8 tools** listed
3. If not visible → restart VS Code (the MCP server needs a fresh reload)

### Step 5: Start Using!
Open Copilot Chat (`Ctrl+Shift+I`) and type any Fabric request naturally.

### Team Onboarding Checklist

| Step | Action | Verify |
|------|--------|--------|
| 1 | Clone repo & checkout `feature/mas/dev_v1` | `git branch` shows `feature/mas/dev_v1` |
| 2 | Run `python setup_wizard.py` | All 7 steps show ✅ |
| 3 | `fab auth login` | `fab auth status` shows authenticated |
| 4 | Open VS Code → MCP: List Servers | `fabric-mas` with 8 tools |
| 5 | Copilot Chat → "List all Fabric agents" | Returns 31 agents |

### Step 6: Start the live dashboard server
```powershell
python mas_log_server.py
```
Then open `fabric_mas_visualiser.html` in your browser.
The dashboard auto-refreshes every 5 seconds and shows all agent activity in real time.

> **Requirements:** Python 3.10+, VS Code 1.96+, GitHub Copilot licence (active), Fabric CLI.

---

## Do I Need a Prefix or Special Command?

### Short Answer: **No prefix needed!**

Fabric-MAS works through **VS Code MCP (Model Context Protocol)**. Copilot **automatically discovers** the 8 MCP tools when the server is running — you just type naturally in Copilot Chat.

### How to Talk to Fabric-MAS

| ✅ Just Type This | ❌ You Do NOT Need This |
|-------------------|-------------------------|
| "Create a lakehouse called Bronze" | ~~`@fabric-mas create lakehouse Bronze`~~ |
| "List all agents" | ~~`/mas list agents`~~ |
| "Generate a star schema for sales" | ~~`#data-modeling generate schema`~~ |
| "Set up real-time analytics" | ~~`fabric-mas: set up real-time`~~ |

### Why No Prefix?

When `.vscode/mcp.json` is present and the MCP server is running:
1. **Copilot sees the 8 tools** (execute_fabric_task, run_fabric_agent, etc.)
2. **Copilot reads the tool descriptions** and knows when to use them
3. **Your natural language prompt** is matched to the right tool automatically
4. **The orchestrator's keyword planner** routes to the correct agent(s)

### When Does Copilot Use Fabric-MAS vs Normal Response?

| Your Prompt | Copilot's Decision |
|------------|--------------------|
| "Create a lakehouse in workspace X" | → Uses `execute_fabric_task` MCP tool |
| "What agents are available?" | → Uses `list_available_agents` MCP tool |
| "What is a lakehouse?" | → Normal Copilot answer (general knowledge) |
| "Generate a star schema" | → Uses `run_fabric_agent` with data-modeling |
| "How do I use Python decorators?" | → Normal Copilot answer (not Fabric-related) |

Copilot is smart enough to route **Fabric management requests** to your MCP tools and answer **general questions** normally.

### Pro Tip: Be Specific
The more specific your prompt, the better the routing:
```
✅ "Create a lakehouse named Bronze_Sales in workspace abc-123"
✅ "Generate a snowflake schema for inventory with SCD Type 2"
✅ "Deploy pipeline to production workspace"

⚠️ Less specific (still works, but may ask follow-up):
   "Make a lakehouse"
   "Set up analytics"
```

---

## Quick Start (One-Prompt Setup)

The fastest way to get started — run a single command:

```powershell
python setup_wizard.py
```

This script automatically:
1. ✅ Checks Python version (3.10+ required)
2. ✅ Creates a virtual environment (`.venv/`)
3. ✅ Installs all dependencies from `requirements.txt`
4. ✅ Creates `.env` from `.env.example` (no API keys needed!)
5. ✅ Checks Microsoft Fabric CLI (`fab`) installation
6. ✅ Configures `.vscode/mcp.json` for MCP integration
7. ✅ Validates the system (imports, agent count, config)

After setup, open VS Code and start talking to Copilot — it will auto-discover the MCP tools.

---

## Prerequisites

| Requirement | Version | Purpose | Required? |
|------------|---------|---------|-----------|
| Python | 3.10+ | Runtime | ✅ Yes |
| Microsoft Fabric CLI | Latest | `fab` commands for Fabric operations | ✅ Yes |
| VS Code | 1.96+ | IDE with MCP support | ✅ Yes |
| GitHub Copilot | Active licence | LLM for natural language processing | ✅ Yes |
| Tavily API Key | — | Auto-train documentation search | ❌ Optional |

> **No OpenAI API Key needed!** GitHub Copilot (included with your licence) acts as
> the LLM through VS Code MCP integration.

---

## Installation

### 1. Clone the Repository
```powershell
git clone https://github.com/gbadhaniten/DP_FABRIC_MAS.git
cd DP_FABRIC_MAS
git checkout feature/mas/dev_v1
```

### 2. Run the Setup Wizard (Recommended)
```powershell
python setup_wizard.py
```

### Or Manual Setup:

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies (no OpenAI/LangChain needed!)
pip install -r requirements.txt

# Install Fabric CLI
pip install ms-fabric-cli
fab auth login

# Create .env
Copy-Item .env.example .env
```

---

## Configuration

### Create `.env` File
```powershell
Copy-Item .env.example .env
```

Edit `.env`:
```env
# No OpenAI API key needed! GitHub Copilot is the LLM.

# Optional — for auto-train documentation search
TAVILY_API_KEY=tvly-your-tavily-key-here

# Optional — default workspace for all operations
FABRIC_WORKSPACE_ID=your-default-workspace-id

# Start with dry-run mode (no real Fabric changes)
FABRIC_DRY_RUN=true
```

---

## VS Code + Copilot Integration

### How It Works

```
┌──────────────────────────────────┐
│  GitHub Copilot (your LLM)       │
│  Understands natural language     │
│  Has your Copilot licence ✓      │
└──────────┬───────────────────────┘
           │ Calls MCP tools
           ▼
┌──────────────────────────────────┐
│  Fabric-MAS MCP Server           │
│  8 tools for Fabric management   │
│  Keyword-based routing           │
│  31 specialized agents           │
└──────────┬───────────────────────┘
           │ Executes via fab CLI
           ▼
┌──────────────────────────────────┐
│  Microsoft Fabric Platform       │
│  Workspaces, Lakehouses, etc.   │
└──────────────────────────────────┘
```

### MCP Configuration

The setup wizard creates `.vscode/mcp.json` automatically. Or create it manually:

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

### Using Copilot with Fabric-MAS

1. Open VS Code in the FABRIC-MAS folder
2. Open GitHub Copilot Chat (`Ctrl+Shift+I`)
3. MCP tools are auto-discovered — just type naturally:

```
You: "Create a Bronze and Silver lakehouse in workspace abc-123"
Copilot: [Uses execute_fabric_task tool] → Routes to lakehouse-agent → Executes
```

```
You: "Show me all available Fabric agents"
Copilot: [Uses list_available_agents tool] → Returns 31 agents
```

```
You: "Generate a star schema for sales analytics with SCD Type 2"
Copilot: [Uses run_fabric_agent tool with data_modeling agent] → Generates model
```

### Verify MCP Connection
1. Open VS Code Command Palette (`Ctrl+Shift+P`)
2. Run: **MCP: List Servers**
3. You should see `fabric-mas` with 8 tools listed

---

## Agent Activation & Lifecycle

### How Agents Are Activated

Fabric-MAS uses a **lazy auto-discovery** pattern:

```
VS Code starts → MCP server boots → Agents are dormant
    │
User sends prompt via Copilot
    │
Copilot calls MCP tool → _get_orchestrator() creates singleton
    │
orch.auto_register() scans agents/*/ folders → 31 agents registered
    │
Keyword planner identifies agents from prompt → Creates execution plan
    │
_get_agent_instance(key) → Lazy instantiation + knowledge loading
    │
agent.execute(operation, params) → CLI command → Result
    │
Auto-learning: result logged to examples.md
```

### Agent Lifecycle States

| State | Description | When |
|-------|-------------|------|
| **Dormant** | Agent folder exists but nothing loaded | Before first query |
| **Registered** | Class imported into `AgentRegistry` | After `auto_register()` |
| **Active** | Instance created, knowledge loaded | First time plan references agent |
| **Executing** | Running a CLI command or API call | During `agent.execute()` |
| **Learning** | Writing execution results to `examples.md` | After each execution |
| **Cached** | Instance kept in memory for reuse | Between executions |

### What Triggers an Agent?

The keyword planner (or Copilot via `run_fabric_agent`) decides which agents to activate:

```
"Create a lakehouse"       → lakehouse-agent
"Build a star schema"      → data-modeling-agent
"Deploy to production"     → deployment-pipeline-agent
```

---

## Using the 8 MCP Tools

### Tool 1: `execute_fabric_task`
**Main entry point** — takes natural language, plans, and executes.

```
Input: "Create Bronze and Silver lakehouses in workspace abc-123"
→ Keyword planner detects: lakehouse-agent, create operation
→ Executes 2 steps, returns results + workflow HTML
```

### Tool 2: `run_fabric_agent`
**Direct agent execution** — when you know exactly what to do.

```
Input: agent_key="lakehouse", operation="create", params={"display_name": "Bronze"}
→ Bypasses planner, calls LakehouseAgent.create() directly
```

### Tool 3: `list_available_agents`
Returns all 31 registered agents with types, codes, and operations.

### Tool 4: `search_fabric_docs`
Searches Microsoft Fabric documentation via Tavily/Bing.

### Tool 5: `get_agent_knowledge`
Retrieves an agent's knowledge files (instructions, examples, known issues).

### Tool 6: `update_agent_knowledge`
Updates an agent's knowledge files — perfect for customizing guidelines.

```
Input: agent_key="data_modeling", file_name="instructions",
       content="Use prefix 'f_' for facts", mode="append"
→ Appends custom naming convention to data-modeling-agent/instructions.md
```

### Tool 7: `visualize_workflow`
Generates a visual workflow diagram WITHOUT executing (preview mode).

### Tool 8: `get_system_status`
Returns system health: agent count, configuration, tool list.

---

## Example Sessions

### 🏗️ Build a Medallion Architecture
```
Prompt: "Create a medallion architecture with Bronze, Silver, Gold
lakehouses and ETL notebooks in workspace ws-data-prod"

Agents activated: lakehouse-agent (×3), notebook-agent (×2), data-pipeline-agent
```

### 📊 Generate a Data Model
```
Prompt: "Generate a star schema for sales analytics with SCD Type 2
dimensions and output as SQL"

Agent: data-modeling-agent → Generates SQL DDL with fact + dimension tables
```

### 🔧 Update Modeling Guidelines
```
Prompt: "Update our data modeling guidelines: use 'f_' prefix for facts
and 'd_' prefix for dimensions instead of 'Fact_' and 'Dim_'"

Agent: data-modeling-agent → Updates instructions.md with custom conventions
```

### 🔐 Workspace Governance
```
Prompt: "Create workspace Finance-Prod, assign F64 capacity,
configure admin roles"

Agents: workspace + capacity + security
```

---

## Data Modeling Agent

The **Data Modeling Agent** is a specialized agent for dimensional modeling:

### Capabilities
- Generate star/snowflake schema models
- Apply SCD Type 1, 2, or 3
- Enforce naming conventions
- Output as SQL DDL, TMDL, or JSON
- **Updateable guidelines** — customize for your organization

### Update Guidelines
Use the `update_agent_knowledge` MCP tool or tell Copilot:

```
"Update the data modeling guidelines to use our company naming conventions:
tables should use PascalCase, columns snake_case, facts prefixed with 'f_'"
```

The agent reads its `instructions.md` for all modeling decisions, so updating
that file changes all future model generations.

---

## Agent Knowledge System

Each of the 31 agents has co-located knowledge files:

```
agents/lakehouse-agent/
├── agent.py              # Python code
├── instructions.md       # How the agent behaves — editable
├── examples.md           # Few-shot examples + auto-logged history
└── known_issues.md       # Bugs and workarounds — editable
```

### Auto-Learning
After every execution, results are auto-logged to `examples.md`:
- Per-agent results → each agent's `examples.md`
- Overall task summaries → `orchestrator-agent/examples.md`
- Copilot sees these patterns in future requests for better routing

---

## Customising Agents

### Adding a New Agent

1. Create folder: `fabric_mas/agents/my-item-agent/`
2. Create `agent.py`:
   ```python
   from fabric_mas.core.base_agent import BaseAgent, AgentResult, OperationType

   class MyItemAgent(BaseAgent):
       ITEM_TYPE = "My Item"
       ITEM_CODE = "MI"
       FAB_NOUN = "my-item"
       AGENT_FOLDER_NAME = "my-item-agent"

       def create(self, params): ...
       def update(self, item_id, params): ...
       def delete(self, item_id): ...
       def analyze(self, item_id=None, **kwargs): ...
       def deploy(self, item_id, target, **kwargs): ...
   ```
3. Add `__init__.py`, `instructions.md`, `examples.md`, `known_issues.md`
4. The orchestrator **auto-discovers** it at startup — no manual registration!

---

## Troubleshooting

### MCP Server Won't Start
```powershell
python -c "from fabric_mas.core.orchestrator import Orchestrator; print('OK')"
```

### Agent Not Found
```powershell
python -c "
from fabric_mas.core.orchestrator import Orchestrator
o = Orchestrator()
o.auto_register()
print(o.registry.list_agents())
"
```

### Copilot Not Using MCP Tools
1. Verify `.vscode/mcp.json` exists in the project root
2. Run: `Ctrl+Shift+P` → **MCP: List Servers** → Check `fabric-mas`
3. Restart VS Code if tools aren't showing
4. Ensure GitHub Copilot extension is active

### Fabric CLI Errors
```powershell
fab auth status    # Check authentication
fab auth login     # Re-authenticate
fab workspace list # Test a simple command
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FABRIC_WORKSPACE_ID` | ❌ | — | Default workspace for all operations |
| `TAVILY_API_KEY` | ❌ | — | Tavily search for auto-train |
| `BING_SEARCH_API_KEY` | ❌ | — | Bing fallback for auto-train |
| `FABRIC_DRY_RUN` | ❌ | `false` | Enable dry-run mode (no real changes) |
| `LOG_LEVEL` | ❌ | `INFO` | Logging verbosity |

> **Note:** No `OPENAI_API_KEY` or `OPENAI_MODEL` needed. GitHub Copilot is the LLM!
