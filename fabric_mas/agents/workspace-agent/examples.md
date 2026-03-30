# Workspace Agent — Few-Shot Examples

| # | User Request | Operation | Method |
|---|---|---|---|
| 1 | "List all workspaces" | analyze | REST: GET /workspaces |
| 2 | "Who has access to DIG_FAB_MULTIAGENT?" | analyze (role_assignments) | REST: GET /workspaces/{id}/roleAssignments |
| 3 | "List lakehouses in DIG_FAB_MULTIAGENT" | analyze (list_items) | REST: GET /workspaces/{id}/items?type=Lakehouse |
| 4 | "Resolve workspace DIG_FAB_MULTIAGENT" | analyze (resolve_name) | REST: list → match name → return ID |

## Analyze Mode Examples

### List All Workspaces
```json
{"operation": "analyze", "params": {}}
```

### Role Assignments
```json
{"operation": "analyze", "params": {"role_assignments": true, "workspace_id": "DIG_FAB_MULTIAGENT"}}
```

### List Items by Type
```json
{"operation": "analyze", "params": {"list_items": true, "item_type": "Lakehouse", "workspace_id": "DIG_FAB_MULTIAGENT"}}
```

### Resolve Workspace Name
```json
{"operation": "analyze", "params": {"resolve_name": true, "workspace_name": "DIG_FAB_MULTIAGENT"}}
```


---

# Execution Log (Auto-Appended Below)


### 2026-03-25 13:22 UTC — CREATE [❌ Failed]
**Prompt:** Create a Lakehouse named LH_MAS_TEST in workspace DIG_FAB_MULTIAGENT

**Result:** 'fab' is not recognized as an internal or external command,
operable program or batch file.

---

### 2026-03-25 13:49 UTC — CREATE [❌ Failed]
**Prompt:** Create a Lakehouse called LH_MAS_TEST in workspace WKS-DP-DATA-AGENTS-01

**Result:** 'fab' is not recognized as an internal or external command,
operable program or batch file.

---
