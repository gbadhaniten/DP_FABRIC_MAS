# SQLAnalyticsEndpoint Agent — Few-Shot Examples

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
| 1 | "Create a SQLAnalyticsEndpoint called MyItem in workspace abc-123" | create | `fab sql-endpoint create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all SQLAnalyticsEndpoint items in my workspace" | analyze | `fab sql-endpoint list --workspace-id "abc-123"` |
| 3 | "Show details of SQLAnalyticsEndpoint item-456" | analyze | `fab sql-endpoint show --sql-endpoint-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the SQLAnalyticsEndpoint named OldItem" | delete | `fab sql-endpoint delete --sql-endpoint-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy SQLAnalyticsEndpoint to production workspace" | deploy | `fab sql-endpoint deploy --sql-endpoint-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

