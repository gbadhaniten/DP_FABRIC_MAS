# Eventhouse Agent — Few-Shot Examples

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
| 1 | "Create a Eventhouse called MyItem in workspace abc-123" | create | `fab eventhouse create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all Eventhouse items in my workspace" | analyze | `fab eventhouse list --workspace-id "abc-123"` |
| 3 | "Show details of Eventhouse item-456" | analyze | `fab eventhouse show --eventhouse-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the Eventhouse named OldItem" | delete | `fab eventhouse delete --eventhouse-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy Eventhouse to production workspace" | deploy | `fab eventhouse deploy --eventhouse-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

