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

## Example 2: Set Up a Real-Time Analytics Pipeline

**User Prompt:**
> I need a real-time analytics setup with an eventhouse, eventstream, and a KQL dashboard in workspace ws-rt-456

**Expected Plan:**
```json
{
  "steps": [
    {
      "agent_key": "eventhouse",
      "operation": "create",
      "params": {"display_name": "RTAnalyticsEventhouse", "workspace_id": "ws-rt-456"},
      "description": "Create Eventhouse for real-time data storage"
    },
    {
      "agent_key": "eventstream",
      "operation": "create",
      "params": {"display_name": "RTAnalyticsStream", "workspace_id": "ws-rt-456"},
      "description": "Create Eventstream to ingest real-time events"
    },
    {
      "agent_key": "kql_database",
      "operation": "create",
      "params": {"display_name": "RTAnalyticsKQL", "workspace_id": "ws-rt-456", "eventhouse_id": "{{step1.result.id}}"},
      "description": "Create KQL Database linked to the Eventhouse"
    },
    {
      "agent_key": "realtime_dashboard",
      "operation": "create",
      "params": {"display_name": "RTDashboard", "workspace_id": "ws-rt-456"},
      "description": "Create Real-Time Dashboard for live monitoring"
    }
  ],
  "metadata": {"assumptions": ["Eventstream will be configured to route events to the KQL Database"]}
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

