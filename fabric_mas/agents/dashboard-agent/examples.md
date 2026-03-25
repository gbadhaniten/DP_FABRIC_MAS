# Dashboard Agent — Few-Shot Examples

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
| 1 | "Create a Dashboard called MyItem in workspace abc-123" | create | `fab dashboard create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all Dashboard items in my workspace" | analyze | `fab dashboard list --workspace-id "abc-123"` |
| 3 | "Show details of Dashboard item-456" | analyze | `fab dashboard show --dashboard-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the Dashboard named OldItem" | delete | `fab dashboard delete --dashboard-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy Dashboard to production workspace" | deploy | `fab dashboard deploy --dashboard-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

