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

| # | User Request | Operation | Method |
|---|---|---|---|
| 1 | "Create a pipeline called PL_ETL" | create | REST: POST /workspaces/{ws}/items |
| 2 | "List all pipelines" | analyze | REST: GET /workspaces/{ws}/items?type=DataPipeline |
| 3 | "Delete pipeline PL_OLD" | delete | REST: find by name → DELETE /workspaces/{ws}/items/{id} |
| 4 | "Create pipeline to copy from WS_A/LH_X to WS_B/LH_Y" | create+copy | REST: create + updateDefinition |

## Cross-Workspace Copy Activity Examples

### Example 1: Explicit workspace/item references
**Prompt:** "Create a pipeline to copy from DIGITEAM_FAB_SELFSERVICE_PUBLIC/LH_MDM_SECURITY to DIG_FAB_MULTIAGENT/LH_MDM"

**Extracted params:**
```json
{
  "source_workspace": "DIGITEAM_FAB_SELFSERVICE_PUBLIC",
  "source_item": "LH_MDM_SECURITY",
  "sink_workspace": "DIG_FAB_MULTIAGENT",
  "sink_item": "LH_MDM",
  "display_name": "PL_COPY_MDM_SECURITY_TO_MDM"
}
```

**Steps:**
1. Create pipeline shell via REST
2. Resolve source workspace → `e1f4d38c-b568-495b-99ae-e6e85e521ff3`
3. Find `LH_MDM_SECURITY` in source workspace → get item ID
4. Resolve sink workspace → `8952abd5-c851-4c8c-a6ba-2748519aebe3`
5. Find `LH_MDM` in sink workspace → get item ID
6. Build Copy Activity JSON with `build_copy_activity()`
7. Build definition with `build_pipeline_definition()`
8. Call `updateDefinition` API

### Example 2: Items in same workspace
**Prompt:** "Create pipeline to copy from LH_RAW to LH_BRONZE"

**Extracted params:**
```json
{
  "source_item": "LH_RAW",
  "sink_item": "LH_BRONZE",
  "display_name": "PL_COPY_RAW_TO_BRONZE"
}
```

### Example 3: "from X in workspace Y" pattern
**Prompt:** "Create a pipeline to copy from LH_SOURCE in WS_DEV to LH_TARGET in WS_PROD"

**Extracted params:**
```json
{
  "source_item": "LH_SOURCE",
  "source_workspace": "WS_DEV",
  "sink_item": "LH_TARGET",
  "sink_workspace": "WS_PROD"
}
```

---

# Execution Log (Auto-Appended Below)


### 2026-03-31 09:02 UTC — CREATE [✅ Success]
**Prompt:** 

**Result:** DataPipeline 'PL_COPY_MDM_SECURITY_TO_MDM' created in workspace 8952abd5-c851-4c8c-a6ba-2748519aebe3

---

### 2026-03-31 09:16 UTC — CREATE [✅ Success]
**Prompt:** [Direct] create data_pipeline with {"display_name": "PL_COPY_MDM_SECURITY_TO_MDM", "workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3", "item_id": "1b89538e-6145-42dc-bd08-37d4084eda2b", "description": "Copies all tables from LH_MDM_SECURITY (DIGITEAM_FAB_SELFSERVICE_PUBLIC) to LH_MDM (DIG_FAB_MULTIAGENT) using ForEach + Copy Activity pattern", "source_workspace_id": "e1f4d38c-b568-495b-99ae-e6e85e521ff3", "source_lakehouse_name": "LH_MDM_SECURITY", "sink_workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3", "sink_lakehouse_id": "36281c04-d17a-4e32-91f3-a4f992fa2453", "sink_lakehouse_name": "LH_MDM", "pattern": "foreach_copy_all_tables", "activities": [{"type": "GetMetadata", "name": "GetTableList", "description": "Get all table names from source lakehouse LH_MDM_SECURITY", "source_lakehouse": "LH_MDM_SECURITY", "field_list": ["childItems"]}, {"type": "ForEach", "name": "ForEach_Table", "items": "@activity('GetTableList').output.childItems", "activities": [{"type": "Copy", "name": "CopyActivity", "source": {"type": "LakehouseTable", "lakehouse": "LH_MDM_SECURITY", "workspace_id": "e1f4d38c-b568-495b-99ae-e6e85e521ff3", "table_name": "@item().name"}, "sink": {"type": "LakehouseTable", "lakehouse": "LH_MDM", "lakehouse_id": "36281c04-d17a-4e32-91f3-a4f992fa2453", "workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3", "table_name": "@item().name", "table_action": "Overwrite"}}]}]}

**Result:** DataPipeline 'PL_COPY_MDM_SECURITY_TO_MDM' created in workspace 8952abd5-c851-4c8c-a6ba-2748519aebe3

---

### 2026-03-31 09:21 UTC — CREATE [❌ Failed]
**Prompt:** [Direct] create data_pipeline with {"display_name": "PL_COPY_MDM_SECURITY_TO_MDM", "workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3", "item_id": "2c12517a-def6-41d9-b15d-f8e5a420cb6a", "description": "Copies all tables from LH_MDM_SECURITY to LH_MDM using ForEach + Copy Activity", "source_workspace_id": "e1f4d38c-b568-495b-99ae-e6e85e521ff3", "source_workspace": "e1f4d38c-b568-495b-99ae-e6e85e521ff3", "source_item": "LH_MDM_SECURITY", "sink_workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3", "sink_workspace": "8952abd5-c851-4c8c-a6ba-2748519aebe3", "sink_item": "LH_MDM", "sink_lakehouse_id": "36281c04-d17a-4e32-91f3-a4f992fa2453", "activity_pattern": "foreach_copy_all_tables", "table_action": "Overwrite"}

**Result:** Create DataPipeline failed: 

---

### 2026-03-31 09:22 UTC — UPDATE [❌ Failed]
**Prompt:** [Direct] update data_pipeline with {"workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3", "item_id": "2c12517a-def6-41d9-b15d-f8e5a420cb6a", "activity_pattern": "foreach_copy_all_tables", "source_workspace_id": "e1f4d38c-b568-495b-99ae-e6e85e521ff3", "source_item": "LH_MDM_SECURITY", "sink_workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3", "sink_item": "LH_MDM", "sink_lakehouse_id": "36281c04-d17a-4e32-91f3-a4f992fa2453", "table_action": "Overwrite", "activities": "foreach_copy_all_tables"}

**Result:** Update_Definition DataPipeline failed: 

---
