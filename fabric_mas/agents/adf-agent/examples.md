# AzureDataFactory Agent — Few-Shot Examples

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
| 1 | "Create a AzureDataFactory called MyItem in workspace abc-123" | create | `fab adf create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all AzureDataFactory items in my workspace" | analyze | `fab adf list --workspace-id "abc-123"` |
| 3 | "Show details of AzureDataFactory item-456" | analyze | `fab adf show --adf-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the AzureDataFactory named OldItem" | delete | `fab adf delete --adf-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy AzureDataFactory to production workspace" | deploy | `fab adf deploy --adf-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

