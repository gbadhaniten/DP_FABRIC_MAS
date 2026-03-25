# OneLake Agent — Few-Shot Examples

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
| 1 | "Create a OneLake called MyItem in workspace abc-123" | create | `fab onelake create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all OneLake items in my workspace" | analyze | `fab onelake list --workspace-id "abc-123"` |
| 3 | "Show details of OneLake item-456" | analyze | `fab onelake show --onelake-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the OneLake named OldItem" | delete | `fab onelake delete --onelake-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy OneLake to production workspace" | deploy | `fab onelake deploy --onelake-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

