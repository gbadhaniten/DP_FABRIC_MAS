# Fabric-MAS Templates

## Standard Agent Template (agent.py)
```python
from fabric_mas.core.base_agent import AgentResult, BaseAgent, OperationType
from typing import Any, Dict, Optional

class <Item>Agent(BaseAgent):
    ITEM_TYPE = "<Item>"
    ITEM_CODE = "<CODE>"
    FAB_NOUN = "<fab-noun>"
    AGENT_FOLDER_NAME = "<item>-agent"

    def create(self, params: Dict[str, Any]) -> AgentResult: ...
    def update(self, item_id: str, params: Dict[str, Any]) -> AgentResult: ...
    def delete(self, item_id: str) -> AgentResult: ...
    def analyze(self, item_id: Optional[str] = None, **kwargs) -> AgentResult: ...
    def deploy(self, item_id: str, target: str, **kwargs) -> AgentResult: ...
```

## Standard instructions.md Template
```markdown
# <Item> Agent — Instructions

## Identity
You are the <Item> agent. You manage Fabric <Item> resources.

## Fabric REST API
- Base URL: `https://api.fabric.microsoft.com/v1`
- Create: `POST /workspaces/{workspaceId}/<items>`
- Update: `PATCH /workspaces/{workspaceId}/<items>/{itemId}`
- Delete: `DELETE /workspaces/{workspaceId}/<items>/{itemId}`
- List:   `GET /workspaces/{workspaceId}/<items>`
- Get:    `GET /workspaces/{workspaceId}/<items>/{itemId}`

## CLI Commands
- `fab <noun> create --display-name "Name" --workspace-id "id"`
- `fab <noun> list --workspace-id "id"`
- `fab <noun> show --<noun>-id "id" --workspace-id "id"`
- `fab <noun> delete --<noun>-id "id" --workspace-id "id"`

## Rules
1. Always validate workspace_id before operations
2. Use display_name not id for user-facing messages
3. Check known_issues.md before executing
```

## Standard fewshot_examples.md Template
```markdown
# <Item> Agent — Few-Shot Examples

| User Request | Agent Action | CLI Command |
|---|---|---|
| "Create a <item> called X in workspace Y" | create | `fab <noun> create --display-name "X" --workspace-id "Y"` |
| "List all <items>" | analyze | `fab <noun> list --workspace-id "Y"` |
| "Delete <item> abc-123" | delete | `fab <noun> delete --<noun>-id "abc-123"` |
```

## Standard known_issues.md Template
```markdown
# <Item> Agent — Known Issues

| Issue | Severity | Workaround |
|---|---|---|
| (none yet) | — | — |
```
