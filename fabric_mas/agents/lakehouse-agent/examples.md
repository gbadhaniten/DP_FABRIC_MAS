# Lakehouse Agent — Few-Shot Examples

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
| 1 | "Create a Lakehouse called MyItem in workspace abc-123" | create | `fab lakehouse create --display-name "MyItem" --workspace-id "abc-123"` |
| 2 | "List all Lakehouse items in my workspace" | analyze | `fab lakehouse list --workspace-id "abc-123"` |
| 3 | "Show details of Lakehouse item-456" | analyze | `fab lakehouse show --lakehouse-id "item-456" --workspace-id "abc-123"` |
| 4 | "Delete the Lakehouse named OldItem" | delete | `fab lakehouse delete --lakehouse-id "item-456" --workspace-id "abc-123"` |
| 5 | "Deploy Lakehouse to production workspace" | deploy | `fab lakehouse deploy --lakehouse-id "item-456" --target-workspace-id "prod-ws"` |


---

# Execution Log (Auto-Appended Below)


### 2026-03-25 13:22 UTC — CREATE [❌ Failed]
**Prompt:** Create a Lakehouse named LH_MAS_TEST in workspace DIG_FAB_MULTIAGENT

**Result:** 'fab' is not recognized as an internal or external command,
operable program or batch file.

---

### 2026-03-25 13:49 UTC — CREATE [✅ Success]
**Prompt:** Create a Lakehouse called LH_MAS_TEST in workspace WKS-DP-DATA-AGENTS-01

**Result:** Lakehouse 'LH_MAS_TEST' created in workspace WKS-DP-DATA-AGENTS-01

---

### 2026-03-25 14:56 UTC — CREATE [✅ Success]
**Prompt:** Create a Lakehouse called LH_MAS_TEST in workspace DIG_FAB_MULTIAGENT

**Result:** Lakehouse 'LH_MAS_TEST' created in workspace DIG_FAB_MULTIAGENT

---
