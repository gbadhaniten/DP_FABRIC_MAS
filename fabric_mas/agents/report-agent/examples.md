# Report Agent — Few-Shot Examples

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
| 1 | "Create a Report called MyItem in workspace abc-123" | create | `fab report create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all Report items in my workspace" | analyze | `fab report list --workspace-id "abc-123"` |
| 3 | "Show details of Report item-456" | analyze | `fab report show --report-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the Report named OldItem" | delete | `fab report delete --report-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy Report to production workspace" | deploy | `fab report deploy --report-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

