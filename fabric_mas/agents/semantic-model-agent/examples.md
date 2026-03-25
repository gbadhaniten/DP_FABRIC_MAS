# SemanticModel Agent — Few-Shot Examples

Few-shot examples teach the agent how to translate natural language into correct commands.

---

## Structure
```json
{
    "fewShots": [
        {
            "id": "unique-uuid",
            "question": "Natural language question",
            "command": "The correct CLI command or API call"
        }
    ]
}
```

---

## Examples

| # | User Request | Operation | CLI Command |
|---|---|---|---|
| 1 | "Create a SemanticModel called MyItem in workspace abc-123" | create | `fab semantic-model create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all SemanticModel items in my workspace" | analyze | `fab semantic-model list --workspace-id "abc-123"` |
| 3 | "Show details of SemanticModel item-456" | analyze | `fab semantic-model show --semantic-model-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the SemanticModel named OldItem" | delete | `fab semantic-model delete --semantic-model-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy SemanticModel to production workspace" | deploy | `fab semantic-model deploy --semantic-model-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

