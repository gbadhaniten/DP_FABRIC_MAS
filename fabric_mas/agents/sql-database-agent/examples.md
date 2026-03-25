# SQLDatabase Agent — Few-Shot Examples

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
| 1 | "Create a SQLDatabase called MyItem in workspace abc-123" | create | `fab sql-database create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all SQLDatabase items in my workspace" | analyze | `fab sql-database list --workspace-id "abc-123"` |
| 3 | "Show details of SQLDatabase item-456" | analyze | `fab sql-database show --sql-database-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the SQLDatabase named OldItem" | delete | `fab sql-database delete --sql-database-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy SQLDatabase to production workspace" | deploy | `fab sql-database deploy --sql-database-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

