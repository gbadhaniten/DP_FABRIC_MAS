# DataflowGen2 Agent — Few-Shot Examples

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
| 1 | "Create a DataflowGen2 called MyItem in workspace abc-123" | create | `fab dataflow create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all DataflowGen2 items in my workspace" | analyze | `fab dataflow list --workspace-id "abc-123"` |
| 3 | "Show details of DataflowGen2 item-456" | analyze | `fab dataflow show --dataflow-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the DataflowGen2 named OldItem" | delete | `fab dataflow delete --dataflow-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy DataflowGen2 to production workspace" | deploy | `fab dataflow deploy --dataflow-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

