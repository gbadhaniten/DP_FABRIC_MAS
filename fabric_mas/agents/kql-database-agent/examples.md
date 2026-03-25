# KQLDatabase Agent — Few-Shot Examples

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
| 1 | "Create a KQLDatabase called MyItem in workspace abc-123" | create | `fab kql-database create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all KQLDatabase items in my workspace" | analyze | `fab kql-database list --workspace-id "abc-123"` |
| 3 | "Show details of KQLDatabase item-456" | analyze | `fab kql-database show --kql-database-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the KQLDatabase named OldItem" | delete | `fab kql-database delete --kql-database-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy KQLDatabase to production workspace" | deploy | `fab kql-database deploy --kql-database-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

