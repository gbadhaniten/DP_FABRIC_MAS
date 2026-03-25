# SparkJobDefinition Agent — Few-Shot Examples

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
| 1 | "Create a SparkJobDefinition called MyItem in workspace abc-123" | create | `fab spark-job-definition create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all SparkJobDefinition items in my workspace" | analyze | `fab spark-job-definition list --workspace-id "abc-123"` |
| 3 | "Show details of SparkJobDefinition item-456" | analyze | `fab spark-job-definition show --spark-job-definition-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the SparkJobDefinition named OldItem" | delete | `fab spark-job-definition delete --spark-job-definition-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy SparkJobDefinition to production workspace" | deploy | `fab spark-job-definition deploy --spark-job-definition-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)

