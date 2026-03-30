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

| # | User Request | Operation | Method |
|---|---|---|---|
| 1 | "Create a Lakehouse called LH_SALES" | create | REST: POST /workspaces/{ws}/items |
| 2 | "List all lakehouses" | analyze | REST: GET /workspaces/{ws}/items?type=Lakehouse |
| 3 | "Delete LH_MAS_TEST" | delete | REST: find by name → DELETE /items/{id} |
| 4 | "Find LH_MDM_SECURITY across workspaces" | find_by_name | REST: iterate workspaces → list items → match |

## Delete by Name Example
**Prompt:** "Delete LH_MAS_TEST"
**Steps:**
1. Search workspace for Lakehouse named "LH_MAS_TEST"
2. Get item ID from search result
3. REST: DELETE /workspaces/{ws}/items/{itemId}

## Find Across Workspaces Example
**Prompt:** "Find LH_MDM_SECURITY"
**Steps:**
1. List all accessible workspaces
2. For each workspace, list Lakehouse items
3. Match display name (case-insensitive)
4. Return item metadata + workspace info


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

### 2026-03-30 08:42 UTC — CREATE [✅ Success]
**Prompt:** Create a Lakehouse called MDM in workspace DIG_FAB_MULTIAGENT

**Result:** Lakehouse 'LH_MDM' created in workspace DIG_FAB_MULTIAGENT

---
