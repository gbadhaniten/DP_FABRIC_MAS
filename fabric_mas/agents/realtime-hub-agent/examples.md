# RealTimeHub Agent — Few-Shot Examples

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
| 1 | "Create a RealTimeHub called MyItem in workspace abc-123" | create | `fab realtime-hub create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all RealTimeHub items in my workspace" | analyze | `fab realtime-hub list --workspace-id "abc-123"` |
| 3 | "Show details of RealTimeHub item-456" | analyze | `fab realtime-hub show --realtime-hub-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the RealTimeHub named OldItem" | delete | `fab realtime-hub delete --realtime-hub-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy RealTimeHub to production workspace" | deploy | `fab realtime-hub deploy --realtime-hub-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

