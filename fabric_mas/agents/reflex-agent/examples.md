# Reflex Agent — Few-Shot Examples

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
| 1 | "Create a Reflex called MyItem in workspace abc-123" | create | `fab reflex create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all Reflex items in my workspace" | analyze | `fab reflex list --workspace-id "abc-123"` |
| 3 | "Show details of Reflex item-456" | analyze | `fab reflex show --reflex-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the Reflex named OldItem" | delete | `fab reflex delete --reflex-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy Reflex to production workspace" | deploy | `fab reflex deploy --reflex-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

