# KQLQueryset Agent — Few-Shot Examples

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
| 1 | "Create a KQLQueryset called MyItem in workspace abc-123" | create | `fab kql-queryset create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all KQLQueryset items in my workspace" | analyze | `fab kql-queryset list --workspace-id "abc-123"` |
| 3 | "Show details of KQLQueryset item-456" | analyze | `fab kql-queryset show --kql-queryset-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the KQLQueryset named OldItem" | delete | `fab kql-queryset delete --kql-queryset-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy KQLQueryset to production workspace" | deploy | `fab kql-queryset deploy --kql-queryset-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

