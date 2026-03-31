# Orchestrator Agent — Few-Shot Examples

## Example 1: Create a Medallion Lakehouse Architecture

**User Prompt:**
> Create a Bronze, Silver, and Gold lakehouse in workspace ws-abc-123

**Expected Plan:**
```json
{
  "steps": [
    {
      "agent_key": "lakehouse",
      "operation": "create",
      "params": {"display_name": "Bronze", "workspace_id": "ws-abc-123"},
      "description": "Create Bronze lakehouse for raw data"
    },
    {
      "agent_key": "lakehouse",
      "operation": "create",
      "params": {"display_name": "Silver", "workspace_id": "ws-abc-123"},
      "description": "Create Silver lakehouse for cleansed data"
    },
    {
      "agent_key": "lakehouse",
      "operation": "create",
      "params": {"display_name": "Gold", "workspace_id": "ws-abc-123"},
      "description": "Create Gold lakehouse for curated data"
    }
  ],
  "metadata": {"assumptions": []}
}
```

---

## Example 2: Set Up Workspace Governance

**User Prompt:**
> Set up workspace Finance-Prod with F64 capacity, admin roles, and connect to DevOps

**Expected Plan:**
```json
{
  "steps": [
    {
      "agent_key": "workspace",
      "operation": "create",
      "params": {"display_name": "Finance-Prod"},
      "description": "Create Finance-Prod workspace"
    },
    {
      "agent_key": "capacity",
      "operation": "assign",
      "params": {"workspace_id": "{{step1.result.id}}", "sku": "F64"},
      "description": "Assign F64 capacity to workspace"
    },
    {
      "agent_key": "security",
      "operation": "assign",
      "params": {"workspace_id": "{{step1.result.id}}", "role": "Admin", "group": "IT Team"},
      "description": "Configure admin RBAC roles"
    },
    {
      "agent_key": "git_integration",
      "operation": "connect",
      "params": {"workspace_id": "{{step1.result.id}}", "repo": "AzureDevOps"},
      "description": "Connect workspace to DevOps repository"
    }
  ],
  "metadata": {"assumptions": ["F64 capacity is available in the tenant"]}
}
```

---

## Example 3: Deploy a Report to Production

**User Prompt:**
> Deploy the Sales Report from dev to production pipeline

**Expected Plan:**
```json
{
  "steps": [
    {
      "agent_key": "deployment_pipeline",
      "operation": "deploy",
      "params": {"item_id": "Sales Report", "target": "production", "source_stage": "development"},
      "description": "Promote Sales Report from dev to production via deployment pipeline"
    }
  ],
  "metadata": {"assumptions": ["A deployment pipeline already exists with dev and production stages"]}
}
```

---

## Example 4: Analyze Workspace Usage

**User Prompt:**
> Show me what's in workspace ws-data-789

**Expected Plan:**
```json
{
  "steps": [
    {
      "agent_key": "workspace",
      "operation": "analyze",
      "params": {"workspace_id": "ws-data-789"},
      "description": "List and analyze all items in the workspace"
    }
  ],
  "metadata": {"assumptions": []}
}
```

---

## Example 5: Multi-Step Notebook + Pipeline Setup

**User Prompt:**
> Create an ETL notebook called TransformSales and a pipeline called SalesPipeline that runs it daily in workspace ws-etl-100

**Expected Plan:**
```json
{
  "steps": [
    {
      "agent_key": "notebook",
      "operation": "create",
      "params": {"display_name": "TransformSales", "workspace_id": "ws-etl-100"},
      "description": "Create ETL notebook for sales data transformation"
    },
    {
      "agent_key": "data_pipeline",
      "operation": "create",
      "params": {
        "display_name": "SalesPipeline",
        "workspace_id": "ws-etl-100",
        "schedule": "daily",
        "notebook_ref": "TransformSales"
      },
      "description": "Create data pipeline that runs TransformSales notebook daily"
    }
  ],
  "metadata": {"assumptions": ["Pipeline will be configured with a daily trigger after creation"]}
}
```


---

# Execution Log (Auto-Appended Below)


### 2026-03-25 13:22 UTC — ORCHESTRATION [❌ Partial Failure]
**Prompt:** Create a Lakehouse named LH_MAS_TEST in workspace DIG_FAB_MULTIAGENT

**Agents Used:** lakehouse, workspace

**Steps:** 2 | **Succeeded:** 0 | **Failed:** 2

---

### 2026-03-25 13:49 UTC — ORCHESTRATION [❌ Partial Failure]
**Prompt:** Create a Lakehouse called LH_MAS_TEST in workspace WKS-DP-DATA-AGENTS-01

**Agents Used:** lakehouse, workspace

**Steps:** 2 | **Succeeded:** 1 | **Failed:** 1

---

### 2026-03-25 14:56 UTC — ORCHESTRATION [✅ All Succeeded]
**Prompt:** Create a Lakehouse called LH_MAS_TEST in workspace DIG_FAB_MULTIAGENT

**Agents Used:** lakehouse

**Steps:** 1 | **Succeeded:** 1 | **Failed:** 0

---

### 2026-03-30 08:42 UTC — ORCHESTRATION [✅ All Succeeded]
**Prompt:** Create a Lakehouse called MDM in workspace DIG_FAB_MULTIAGENT

**Agents Used:** lakehouse

**Steps:** 1 | **Succeeded:** 1 | **Failed:** 0

---

### 2026-03-31 07:41 UTC — ORCHESTRATION [✅ All Succeeded]
**Prompt:** {"steps": [{"agent_key": "dummy", "operation": "create", "params": {"display_name": "demo_item"}, "description": "Create dummy"}], "metadata": {}}

**Agents Used:** dummy

**Steps:** 1 | **Succeeded:** 1 | **Failed:** 0

---

### 2026-03-31 07:41 UTC — ORCHESTRATION [✅ All Succeeded]
**Prompt:** {"steps": [{"agent_key": "dummy", "operation": "create", "params": {"display_name": "demo_item"}, "description": "Create dummy"}], "metadata": {}}

**Agents Used:** dummy

**Steps:** 1 | **Succeeded:** 1 | **Failed:** 0

---

### 2026-03-31 09:02 UTC — ORCHESTRATION [✅ All Succeeded]
**Prompt:** {"steps": [
  {
    "agent_key": "data_pipeline",
    "operation": "create",
    "description": "Create pipeline PL_COPY_MDM_SECURITY_TO_MDM in workspace DIG_FAB_MULTIAGENT (8952abd5-c851-4c8c-a6ba-2748519aebe3) with a ForEach loop over all tables in LH_MDM_SECURITY from source workspace DIGITEAM_FAB_SELFSERVICE_PUBLIC (e1f4d38c-b568-495b-99ae-e6e85e521ff3), with a Copy Activity inside the ForEach that copies each table to LH_MDM (36281c04-d17a-4e32-91f3-a4f992fa2453) in DIG_FAB_MULTIAGENT. The pipeline already exists as item 1b89538e-6145-42dc-bd08-37d4084eda2b — update its definition with the ForEach + Copy Activity pattern. Source type: LakehouseTable. Sink type: LakehouseTable. Use @item().name for dynamic table names in both source and sink.",
    "params": {
      "workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3",
      "display_name": "PL_COPY_MDM_SECURITY_TO_MDM",
      "item_id": "1b89538e-6145-42dc-bd08-37d4084eda2b",
      "source_workspace_id": "e1f4d38c-b568-495b-99ae-e6e85e521ff3",
      "source_lakehouse": "LH_MDM_SECURITY",
      "sink_workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3",
      "sink_lakehouse_id": "36281c04-d17a-4e32-91f3-a4f992fa2453",
      "sink_lakehouse": "LH_MDM",
      "activity_pattern": "foreach_copy_all_tables"
    }
  }
]}

**Agents Used:** data_pipeline

**Steps:** 1 | **Succeeded:** 1 | **Failed:** 0

---
