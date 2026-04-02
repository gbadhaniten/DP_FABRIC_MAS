# 🏗️ ARCHITECTURE — Fabric Multi-Agent System (Fabric-MAS)

> **Copilot-Native**: GitHub Copilot is the LLM. No OpenAI API key required.

## 1) What this system is

Fabric-MAS is a Python multi-agent orchestration layer for Microsoft Fabric operations.
It exposes MCP tools that Copilot can call directly from VS Code and routes requests to
specialized agents for data engineering, integration, analytics, governance, and AI workflows.

Core behavior:
- Natural-language request → orchestrator planning/routing
- REST-first execution (`FabricRestClient`) with CLI fallback (`fab`)
- Dependency-aware multi-step runs with parallel execution for independent tiers
- Agent knowledge loop (`instructions.md`, `examples.md`, `known_issues.md`)

---

## 2) High-level runtime flow

```text
GitHub Copilot Chat
  → MCP Server (mcp_server.py)
  → Orchestrator (fabric_mas/core/orchestrator.py)
  → Agent Registry + Agent Instances
  → REST / CLI execution
  → Telemetry + workflow visual output
```

---

## 3) MCP tools (current)

`mcp_server.py` exposes **9 tools**:
1. `execute_fabric_task`
2. `run_fabric_agent`
3. `list_available_agents`
4. `search_fabric_docs`
5. `get_agent_knowledge`
6. `update_agent_knowledge`
7. `visualize_workflow`
8. `get_system_status`
9. `check_naming_convention`

---

## 4) Agent landscape (current)

The system auto-discovers agent implementations from `fabric_mas/agents/*-agent/agent.py`.

Current roster: **29 agents**

### Data Engineering
- onelake
- lakehouse
- shortcut
- notebook
- spark_job_definition

### Data Integration
- data_pipeline
- copy_job
- azure_data_factory

### Analytics
- warehouse
- sql_endpoint
- sql_database
- mirrored_database

### Real-Time
- kql_queryset
- data_activator

### Governance & Administration
- workspace
- capacity
- deployment_pipeline
- git_integration
- lineage
- monitoring
- variable_library
- security

### AI & Advanced
- data_agent
- copilot
- graphql_api
- user_data_functions
- data_wrangler

### Modeling + Meta
- data_modeling
- orchestrator

---

## 5) Orchestration model

### Planning priority
1. Direct execution (`run_fabric_agent`) when agent + operation are explicit
2. Structured plan execution (`plan_from_json` path)
3. Natural-language orchestration (`execute_fabric_task`) as fallback

### Dependency tiers
Execution is tiered with parallelism inside each tier:
- Tier 0: workspaces
- Tier 1: lakehouses
- Tier 2: notebooks / pipelines
- Tier 3: warehouses
- Tier 4: git integration

If any step in a tier fails, subsequent tiers stop.

---

## 6) Knowledge and learning system

Each agent maintains:
- `instructions.md` (behavior and guidance)
- `examples.md` (examples + execution memory)
- `known_issues.md` (workarounds and recurring failures)

The orchestrator and agents leverage this for smarter repeated execution and safer retries.

---

## 7) Prompt and documentation governance

### Canonical prompt file policy
- Keep exactly **one** top-level prompt catalogue file: `SAMPLE_PROMPTS.md`
- `MASTER_PROMPT.md` is deprecated and removed from active documentation flow

`SAMPLE_PROMPTS.md` must include:
- small scenarios (single-agent)
- medium scenarios (multi-agent)
- complex end-to-end scenarios
- audit/validation prompts

### Architecture update policy (mandatory)
Whenever architecture changes, update this file in the same PR/commit for any of:
- MCP tool additions/removals
- agent roster changes
- routing/dependency/parallel execution behavior changes
- telemetry/visualization behavior changes
- repository structure changes affecting execution paths

Recommended checklist for architecture changes:
1. Update `ARCHITECTURE.md`
2. Update `HOW_TO_USE.md`
3. Update `SAMPLE_PROMPTS.md` (if user-facing behavior changed)
4. Run smoke audit (imports + agent registration + docs consistency grep)

---

## 8) Repository map (critical files)

```text
FABRIC-MAS/
├── mcp_server.py
├── mas_log_server.py
├── setup_wizard.py
├── ARCHITECTURE.md
├── HOW_TO_USE.md
├── SAMPLE_PROMPTS.md
├── MEMORY.md
├── requirements.txt
└── fabric_mas/
    ├── core/
    │   ├── orchestrator.py
    │   ├── base_agent.py
    │   ├── cli_wrapper.py
    │   └── fabric_rest_client.py
    ├── agents/
    └── tools/
```

---

## 9) Current design principles

- Keep orchestration deterministic and dependency-safe
- Prefer REST to reduce CLI fragility
- Keep prompt surface simple and user-oriented
- Keep agent knowledge local, explicit, and append-only for operational history
- Keep docs synchronized with architecture as a release gate
