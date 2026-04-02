# 🧠 MEMORY — Fabric-MAS Portable Knowledge Base

> Purpose: a single long-term memory file for understanding, operating, and reproducing Fabric-MAS in another environment.

---

## 1) What Fabric-MAS is

Fabric-MAS is a Copilot-native multi-agent control plane for Microsoft Fabric.
It lets users manage Fabric resources using natural language from VS Code Chat.

It provides:
- MCP tool surface for Copilot integration
- Orchestrator for routing and execution planning
- 29 specialized Fabric agents
- REST-first operations with CLI fallback
- execution telemetry and workflow visualization
- agent-level knowledge files for operational memory

---

## 2) Why this solution exists

Primary goals:
- standardize Fabric operations through one conversational interface
- reduce repetitive manual setup and admin workflows
- enforce naming, sequencing, and deployment discipline
- support end-to-end data engineering workflows (small to enterprise-scale)
- make knowledge persistent and reusable across team members

---

## 3) System architecture summary

```text
Copilot Chat
  → MCP Server (`mcp_server.py`)
  → Orchestrator (`fabric_mas/core/orchestrator.py`)
  → Agent registry + agent execution
  → Fabric REST APIs / Fabric CLI
  → Telemetry + visual workflow output
```

Execution style:
- route preference: direct agent call > structured plan > natural-language plan
- dependency-aware tiering
- parallel execution for independent tier members
- fail-fast between tiers

---

## 4) Current capabilities snapshot

### MCP tools (9)
1. execute_fabric_task
2. run_fabric_agent
3. list_available_agents
4. search_fabric_docs
5. get_agent_knowledge
6. update_agent_knowledge
7. visualize_workflow
8. get_system_status
9. check_naming_convention

### Agent roster (29)
- Data Engineering: onelake, lakehouse, shortcut, notebook, spark_job_definition
- Data Integration: data_pipeline, copy_job, azure_data_factory
- Analytics: warehouse, sql_endpoint, sql_database, mirrored_database
- Real-Time: kql_queryset, data_activator
- Governance: workspace, capacity, deployment_pipeline, git_integration, lineage, monitoring, variable_library, security
- AI/Advanced: data_agent, copilot, graphql_api, user_data_functions, data_wrangler
- Modeling/Meta: data_modeling, orchestrator

---

## 5) Key design decisions

1. Copilot-native orchestration instead of external LLM API dependency
2. REST-first operations for reliability and modern API support
3. local knowledge files for transparent and auditable behavior
4. convention-driven naming and deployment guardrails
5. pluggable folder-based agent auto-discovery

---

## 6) Core files to replicate elsewhere

Top-level required:
- `mcp_server.py`
- `setup_wizard.py`
- `mas_log_server.py`
- `requirements.txt`
- `.vscode/mcp.json`
- `ARCHITECTURE.md`
- `HOW_TO_USE.md`
- `SAMPLE_PROMPTS.md`
- `MEMORY.md`

Package required:
- `fabric_mas/core/*`
- `fabric_mas/tools/*`
- `fabric_mas/agents/*-agent/*`

---

## 7) How to replicate this solution in another repo

1. Copy the structure above.
2. Create and activate venv.
3. Install dependencies from `requirements.txt`.
4. Configure `.vscode/mcp.json` to run `python mcp_server.py`.
5. Authenticate Fabric CLI (`fab auth login`).
6. Run smoke checks:
   - orchestrator import
   - auto-register count
   - compileall
7. Verify MCP tools in VS Code (`MCP: List Servers`).

---

## 8) How to ask external AI tools about this solution

When asking ChatGPT/Claude/etc., share:
- this file (`MEMORY.md`)
- `ARCHITECTURE.md`
- `SAMPLE_PROMPTS.md`
- one or two agent folders relevant to your question

Suggested question template:

```text
I have a Copilot-native Fabric multi-agent system with MCP server, orchestrator, and 29 Fabric agents.
Given the attached architecture and memory docs, suggest improvements for:
<topic: reliability / deployment / scaling / governance / cost / observability>.
Return prioritized actions with low-risk implementation order.
```

---

## 9) Change history highlights (current state)

- removed deprecated/unused agent families
- normalized system to 29 active agents
- upgraded orchestrator with dependency-tiered parallel execution
- updated docs to single prompt source (`SAMPLE_PROMPTS.md`)
- aligned workflow visualizer and docs with active agent set

---

## 10) Operational guardrails

- validate naming before create operations
- require explicit confirmation for prod-destructive actions
- stop execution on tier failure
- keep `examples.md` append-only for execution traceability
- update architecture/how-to/prompts together for major changes

---

## 11) Documentation governance policy

When architecture changes, update all in same PR:
1. `ARCHITECTURE.md`
2. `HOW_TO_USE.md`
3. `SAMPLE_PROMPTS.md`
4. `MEMORY.md` (if capability, purpose, or design changed)

---

## 12) Recommended next improvements

1. add CI smoke test for agent registration and stale-reference grep
2. add contract tests for MCP tool schema behavior
3. add structured telemetry persistence (JSONL/SQLite)
4. add doc consistency validator to fail PRs on outdated counts/tool lists
5. add optional dry-run integration test suite for critical multi-agent workflows
