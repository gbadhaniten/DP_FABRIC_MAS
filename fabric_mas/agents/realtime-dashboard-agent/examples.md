# RealTimeDashboard Agent — Few-Shot Examples

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
| 1 | "Create a RealTimeDashboard called MyItem in workspace abc-123" | create | `fab realtime-dashboard create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all RealTimeDashboard items in my workspace" | analyze | `fab realtime-dashboard list --workspace-id "abc-123"` |
| 3 | "Show details of RealTimeDashboard item-456" | analyze | `fab realtime-dashboard show --realtime-dashboard-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the RealTimeDashboard named OldItem" | delete | `fab realtime-dashboard delete --realtime-dashboard-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy RealTimeDashboard to production workspace" | deploy | `fab realtime-dashboard deploy --realtime-dashboard-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

