# PowerBIApp Agent — Few-Shot Examples

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
| 1 | "Create a PowerBIApp called MyItem in workspace abc-123" | create | `fab app create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all PowerBIApp items in my workspace" | analyze | `fab app list --workspace-id "abc-123"` |
| 3 | "Show details of PowerBIApp item-456" | analyze | `fab app show --app-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the PowerBIApp named OldItem" | delete | `fab app delete --app-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy PowerBIApp to production workspace" | deploy | `fab app deploy --app-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

