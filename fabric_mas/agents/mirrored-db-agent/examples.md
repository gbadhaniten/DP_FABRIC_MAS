# MirroredDatabase Agent — Few-Shot Examples

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
| 1 | "Create a MirroredDatabase called MyItem in workspace abc-123" | create | `fab mirrored-database create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all MirroredDatabase items in my workspace" | analyze | `fab mirrored-database list --workspace-id "abc-123"` |
| 3 | "Show details of MirroredDatabase item-456" | analyze | `fab mirrored-database show --mirrored-database-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the MirroredDatabase named OldItem" | delete | `fab mirrored-database delete --mirrored-database-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy MirroredDatabase to production workspace" | deploy | `fab mirrored-database deploy --mirrored-database-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

