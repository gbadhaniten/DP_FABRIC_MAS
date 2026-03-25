# DataActivator Agent — Few-Shot Examples

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
| 1 | "Create a DataActivator called MyItem in workspace abc-123" | create | `fab data-activator create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all DataActivator items in my workspace" | analyze | `fab data-activator list --workspace-id "abc-123"` |
| 3 | "Show details of DataActivator item-456" | analyze | `fab data-activator show --data-activator-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the DataActivator named OldItem" | delete | `fab data-activator delete --data-activator-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy DataActivator to production workspace" | deploy | `fab data-activator deploy --data-activator-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

