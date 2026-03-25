# DataPipeline Agent — Few-Shot Examples

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
| 1 | "Create a DataPipeline called MyItem in workspace abc-123" | create | `fab data-pipeline create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all DataPipeline items in my workspace" | analyze | `fab data-pipeline list --workspace-id "abc-123"` |
| 3 | "Show details of DataPipeline item-456" | analyze | `fab data-pipeline show --data-pipeline-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the DataPipeline named OldItem" | delete | `fab data-pipeline delete --data-pipeline-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy DataPipeline to production workspace" | deploy | `fab data-pipeline deploy --data-pipeline-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

