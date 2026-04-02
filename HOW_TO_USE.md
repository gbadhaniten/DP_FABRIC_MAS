# 📖 HOW TO USE — Fabric Multi-Agent System (Fabric-MAS)

> **Copilot-Native**: GitHub Copilot is the LLM. No OpenAI API key required.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Install & Configure](#install--configure)
4. [Use from Copilot Chat](#use-from-copilot-chat)
5. [MCP Tools (Current)](#mcp-tools-current)
6. [Common Prompt Patterns](#common-prompt-patterns)
7. [Audit & Smoke Validation](#audit--smoke-validation)
8. [Troubleshooting](#troubleshooting)
9. [Documentation Maintenance Rule](#documentation-maintenance-rule)

---

## Quick Start

```powershell
git clone https://github.com/gbadhaniten/DP_FABRIC_MAS.git
cd DP_FABRIC_MAS
git checkout feature/mas/dev_v1

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

pip install ms-fabric-cli
fab auth login

code .
```

In VS Code:
1. Open Command Palette: `Ctrl+Shift+P`
2. Run `MCP: List Servers`
3. Verify `fabric-mas` is listed with tools

Optional live activity dashboard:
```powershell
python mas_log_server.py
```
Then open `fabric_mas_visualiser.html`.

---

## Prerequisites

- Python 3.10+
- VS Code 1.96+
- Active GitHub Copilot license
- `ms-fabric-cli` installed and authenticated
- Access to target Fabric workspaces

## Install & Configure

### Environment file
```powershell
Copy-Item .env.example .env
```

Recommended `.env` values:
```env
FABRIC_DRY_RUN=true
FABRIC_WORKSPACE_ID=<optional-default-workspace-id>
TAVILY_API_KEY=<optional>
```

### MCP config
Ensure `.vscode/mcp.json` points to:
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

## Use from Copilot Chat

No command prefix is required. Use plain English in Copilot Chat.

Examples:
```text
Create LH_BRONZE_RAW in DIG_CORE_DATA_DEV.
```

```text
Build Bronze/Silver/Gold lakehouses and a daily orchestrator pipeline.
```

```text
Audit failed jobs and RBAC configuration for DIG_CORE_DATA_DEV.
```

## MCP Tools (Current)

Fabric-MAS currently exposes **9 MCP tools**:
1. `execute_fabric_task`
2. `run_fabric_agent`
3. `list_available_agents`
4. `search_fabric_docs`
5. `get_agent_knowledge`
6. `update_agent_knowledge`
7. `visualize_workflow`
8. `get_system_status`
9. `check_naming_convention`

Current auto-discovered agents: **29**.

## Common Prompt Patterns

- Small: single agent, single operation
- Medium: 2–4 agent workflow
- Complex: end-to-end architecture build + audit

Use `SAMPLE_PROMPTS.md` as the **single prompt reference**.

---

## Audit & Smoke Validation

Run these checks after structural/documentation updates:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -c "from fabric_mas.core.orchestrator import Orchestrator; o=Orchestrator(); o.auto_register(); print('Registered agents:', len(o.registry.list_agents()))"
python -m compileall fabric_mas
```

Expectations:
- agent registration count = 29
- compileall returns success
- no unresolved references to removed agents

---

## Troubleshooting

### `ModuleNotFoundError` on startup
Activate venv and reinstall dependencies:
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### MCP server not visible
- Restart VS Code
- Run `MCP: List Servers`
- Validate `.vscode/mcp.json` and Python interpreter selection

### Fabric auth issues
```powershell
fab auth status
fab auth login
```

---

## Documentation Maintenance Rule

Whenever architecture or routing behavior changes, update all three in the same change set:
1. `ARCHITECTURE.md`
2. `HOW_TO_USE.md`
3. `SAMPLE_PROMPTS.md`

Do not keep parallel prompt files. `MASTER_PROMPT.md` is retired.

---

## Agent Activation & Lifecycle (Reference)

Fabric-MAS uses lazy auto-discovery:

```text
VS Code starts → MCP server boots
→ Copilot calls tool
→ orchestrator singleton is created
→ `auto_register()` loads 29 agents
→ plan executes via direct/parallel routing
→ results are logged to agent knowledge
```

State model:
- Dormant
- Registered
- Active
- Executing
- Learning
- Cached

