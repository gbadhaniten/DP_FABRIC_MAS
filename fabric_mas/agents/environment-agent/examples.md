# Environment Agent — Few-Shot Examples

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
| 1 | "Create a Environment called MyItem in workspace abc-123" | create | `fab environment create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all Environment items in my workspace" | analyze | `fab environment list --workspace-id "abc-123"` |
| 3 | "Show details of Environment item-456" | analyze | `fab environment show --environment-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the Environment named OldItem" | delete | `fab environment delete --environment-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy Environment to production workspace" | deploy | `fab environment deploy --environment-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

