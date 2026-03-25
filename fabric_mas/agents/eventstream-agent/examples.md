# Eventstream Agent — Few-Shot Examples

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
| 1 | "Create a Eventstream called MyItem in workspace abc-123" | create | `fab eventstream create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all Eventstream items in my workspace" | analyze | `fab eventstream list --workspace-id "abc-123"` |
| 3 | "Show details of Eventstream item-456" | analyze | `fab eventstream show --eventstream-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the Eventstream named OldItem" | delete | `fab eventstream delete --eventstream-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy Eventstream to production workspace" | deploy | `fab eventstream deploy --eventstream-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

