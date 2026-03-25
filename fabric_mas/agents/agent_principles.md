# Agent Principles — Fabric-MAS
## One Item, One Agent

Every Fabric item type has **exactly one dedicated agent** with its own folder:

```
fabric_mas/agents/<item-name>-agent/
├── __init__.py               # Re-exports the agent class
├── agent.py                  # Agent class (inherits BaseAgent)
├── instructions.md           # Behaviour rules, API references, CLI patterns
├── fewshot_examples.md       # QA pairs: natural language → correct commands
└── known_issues.md           # Bugs, workarounds, edge cases
```

## Naming Convention
| Attribute | Pattern | Example |
|---|---|---|
| Folder | `<item>-agent` | `lakehouse-agent` |
| Class | `<Item>Agent` | `LakehouseAgent` |
| `ITEM_TYPE` | PascalCase | `"Lakehouse"` |
| `ITEM_CODE` | Uppercase short | `"LH"` |
| `FAB_NOUN` | CLI noun | `"lakehouse"` |

## The Five Canonical Operations
Every agent **must** implement:
1. `create(params)` — Provision a new Fabric item
2. `update(item_id, params)` — Modify an existing item
3. `delete(item_id)` — Remove an item
4. `analyze(item_id?, **kwargs)` — Inspect / list items
5. `deploy(item_id, target, **kwargs)` — Promote across environments

## Knowledge Files (.md)
- **instructions.md** — The agent's rulebook. What REST endpoints to hit, which `fab` commands to use, parameter requirements, sequencing rules.
- **fewshot_examples.md** — Pairs of (user question → correct action). The orchestrator's LLM uses these for few-shot prompting to improve accuracy.
- **known_issues.md** — Documented bugs, API quirks, and workarounds. Updated as issues are discovered.

## Autotrain Protocol
Before executing any operation, agents call `_autotrain(operation)` which:
1. Checks the in-memory cache
2. If cache-miss → calls SearchTool (Tavily/Bing) to fetch the latest API spec
3. Caches the result for future calls

## Brain Routing
The Master Brain (orchestrator.py) receives a natural-language prompt, uses an LLM to produce a JSON plan, and dispatches each step to the correct agent via `agent.execute(operation, params)`.
