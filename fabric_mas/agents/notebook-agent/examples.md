# Notebook Agent — Few-Shot Examples

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
| 1 | "Create a Notebook called MyItem in workspace abc-123" | create | `fab notebook create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all Notebook items in my workspace" | analyze | `fab notebook list --workspace-id "abc-123"` |
| 3 | "Show details of Notebook item-456" | analyze | `fab notebook show --notebook-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the Notebook named OldItem" | delete | `fab notebook delete --notebook-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy Notebook to production workspace" | deploy | `fab notebook deploy --notebook-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

