# Orchestrator Agent — Known Issues & Workarounds

## Issue 1: LLM Returns Markdown-Fenced JSON
**Problem:** Some LLM models wrap the JSON plan in ```json ... ``` fences despite instructions.
**Workaround:** The `_parse_plan()` method strips leading/trailing ``` fences automatically.

---

## Issue 2: Agent Key Mismatch
**Problem:** The LLM may use an agent key that doesn't match the registry (e.g., "data-pipeline" instead of "data_pipeline").
**Workaround:** The `AgentRegistry.get()` method normalizes keys by replacing spaces with underscores and lowercasing. Hyphens in folder names are also converted to underscores during auto-registration.

---

## Issue 3: Missing Workspace ID
**Problem:** User forgets to specify a workspace, causing agents to fail with "workspace_id required".
**Workaround:** The orchestrator's `__init__` accepts a default `workspace_id`. If set, it's injected into all steps. The LLM planner prompt also instructs the model to use the workspace when provided.

---

## Issue 4: Step Dependencies Not Resolved
**Problem:** Later steps may depend on outputs of earlier steps (e.g., a Notebook referencing a newly created Lakehouse ID), but the plan uses placeholder references like `{{step1.result.id}}`.
**Workaround:** Currently, `execute_plan()` runs steps sequentially. Future enhancement: parse `{{stepN.result.*}}` placeholders and substitute with actual result data.

---

## Issue 5: langchain-openai ImportError
**Problem:** If `langchain-openai` is not installed, the planner fails.
**Workaround:** The `plan()` method has a fallback `_plan_openai_direct()` that calls the OpenAI API via `requests` directly, bypassing LangChain entirely.

---

## Issue 6: Rate Limiting on LLM API
**Problem:** Rapid successive calls can hit OpenAI rate limits.
**Workaround:** Add exponential backoff. Currently not implemented — users should set appropriate `max_tokens` and avoid batching too many plans in tight loops.

---

## Issue 7: Auto-Registration Import Failures
**Problem:** If an agent folder has a syntax error in `agent.py`, `auto_register()` logs a warning but continues. The broken agent is simply unavailable.
**Workaround:** Check logs for `"Failed to import"` messages. Fix the agent's `agent.py` and restart.
