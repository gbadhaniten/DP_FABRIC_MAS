# CopyJob Agent — Few-Shot Examples

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
| 1 | "Create a CopyJob called MyItem in workspace abc-123" | create | `fab copy-job create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all CopyJob items in my workspace" | analyze | `fab copy-job list --workspace-id "abc-123"` |
| 3 | "Show details of CopyJob item-456" | analyze | `fab copy-job show --copy-job-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the CopyJob named OldItem" | delete | `fab copy-job delete --copy-job-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy CopyJob to production workspace" | deploy | `fab copy-job deploy --copy-job-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

