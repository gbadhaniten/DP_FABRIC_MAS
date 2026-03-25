# Warehouse Agent — Few-Shot Examples

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
| 1 | "Create a Warehouse called MyItem in workspace abc-123" | create | `fab warehouse create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all Warehouse items in my workspace" | analyze | `fab warehouse list --workspace-id "abc-123"` |
| 3 | "Show details of Warehouse item-456" | analyze | `fab warehouse show --warehouse-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the Warehouse named OldItem" | delete | `fab warehouse delete --warehouse-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy Warehouse to production workspace" | deploy | `fab warehouse deploy --warehouse-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

