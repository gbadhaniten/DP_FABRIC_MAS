# 💡 SAMPLE PROMPTS — Fabric Multi-Agent System (Fabric-MAS)

> This is the **single canonical prompt file** for Fabric-MAS.
> It replaces `MASTER_PROMPT.md` and contains small, medium, and complex scenarios.
> Use these directly in GitHub Copilot Chat (Agent mode).

---

## 📂 Table of Contents
1. [Small Scenarios (Single Agent)](#-small-scenarios-single-agent)
2. [Medium Scenarios (2–4 Agents)](#-medium-scenarios-24-agents)
3. [Complex Scenarios (End-to-End)](#-complex-scenarios-end-to-end)
4. [Reusable Prompt Templates](#-reusable-prompt-templates)
5. [Validation & Audit Prompts](#-validation--audit-prompts)

---

## 🟢 Small Scenarios (Single Agent)

### Lakehouse
```text
Create a lakehouse named LH_BRONZE_RAW in workspace DIG_CORE_DATA_DEV.
```

### Notebook
```text
Create a notebook named NB_SILVER_TRANSFORM in workspace DIG_CORE_DATA_DEV.
```

### Data Pipeline
```text
Create a pipeline named PL_DAILY_INGEST in workspace DIG_CORE_DATA_DEV.
```

### Warehouse
```text
Create a warehouse named WH_GOLD_ANALYTICS in workspace DIG_CORE_DATA_DEV.
```

### Security Audit
```text
Analyze workspace access and list role assignments for DIG_CORE_DATA_DEV.
```

### Monitoring
```text
Show failed jobs for workspace DIG_CORE_DATA_DEV in the last 24 hours.
```

---

## 🟡 Medium Scenarios (2–4 Agents)

### Medallion Foundation
```text
In workspace DIG_CORE_DATA_DEV, create LH_BRONZE_RAW, LH_SILVER_CURATED, and LH_GOLD_CONSUMPTION,
then create notebook NB_BRONZE_TO_SILVER and pipeline PL_BRONZE_TO_SILVER to run it.
```

### Warehouse + Data Model
```text
Create WH_SALES_ANALYTICS in DIG_CORE_DATA_DEV, generate a star schema for sales,
and provide SQL DDL to implement it in the warehouse.
```

### Copy + Transform
```text
Create a copy pipeline from DIGITEAM_FAB_SELFSERVICE_PUBLIC/LH_MDM to DIG_CORE_DATA_DEV/LH_BRONZE_RAW,
then create a transformation notebook and pipeline schedule every 6 hours.
```

### Governance Package
```text
For workspace DIG_CORE_DATA_DEV: assign capacity, audit current RBAC, connect Git integration,
and return a summary of configuration drift risks.
```

---

## 🔴 Complex Scenarios (End-to-End)

### End-to-End Data Engineering Platform
```text
Create an end-to-end solution in DIG_CORE_DATA_DEV:
1) Create Bronze, Silver, Gold lakehouses.
2) Create notebooks for Bronze→Silver and Silver→Gold transformations.
3) Create orchestration pipelines with retries and failure notifications.
4) Create WH_GOLD_ANALYTICS from Gold.
5) Generate and apply a sales star schema.
6) Configure RBAC for Data Engineers and Business Analysts.
7) Connect workspace to Git and provide branch strategy.
8) Run a final health audit and return risks + remediation actions.
```

### Cross-Workspace Copy + Promotion
```text
Build cross-workspace movement from DIGITEAM_FAB_SELFSERVICE_PUBLIC/LH_MDM
to DIG_CORE_DATA_DEV/LH_BRONZE_RAW using a copy pipeline.
Then create downstream Silver/Gold processing, warehouse analytics, and
deployment promotion plan Dev→Test→Prod with rollback guidance.
```

### Reliability & Cost Optimization
```text
Audit all pipelines, spark jobs, and capacities in DIG_CORE_DATA_DEV.
Identify top failures, bottlenecks, and cost hotspots.
Implement recommended scheduling, retry, and capacity adjustments,
then produce before/after operational KPIs.
```

---

## 🧱 Reusable Prompt Templates

### Template A — Single Item Create
```text
Create a <item_type> named <PREFIX_NAME> in workspace <WORKSPACE_NAME_OR_ID> with description "<DESC>".
```

### Template B — Multi-Step Build
```text
In workspace <WORKSPACE>, create <ITEM_1>, <ITEM_2>, and <ITEM_3>.
Then configure dependencies so <ITEM_2> reads from <ITEM_1> and <ITEM_3> reads from <ITEM_2>.
Return execution plan, results, and failed-step remediation if any.
```

### Template C — Cross-Workspace Copy
```text
Create a copy pipeline from <SOURCE_WORKSPACE>/<SOURCE_ITEM>
to <SINK_WORKSPACE>/<SINK_ITEM> with pipeline name PL_COPY_<SOURCE>_TO_<SINK>.
Include schedule, retry policy, and monitoring hooks.
```

### Template D — Audit
```text
Run a workspace audit for <WORKSPACE>:
- inventory of items
- RBAC summary
- failed jobs in last <N> days
- deployment risks
- top 5 recommended fixes
```

---

## ✅ Validation & Audit Prompts

```text
List all available agents and categorize them by capability.
```

```text
Validate naming conventions for these items: LH_BRONZE_RAW, NB_ETL_SALES, PL_DAILY_LOAD.
```

```text
Simulate this workflow without execution and show the visual plan:
Create Bronze/Silver/Gold lakehouses, notebook transforms, and one orchestrator pipeline.
```

```text
Run a system status check and show MCP server health, registered agents, and telemetry readiness.
```

---

## Notes

- Use uppercase prefixes where applicable: `LH_`, `NB_`, `PL_`, `WH_`.
- Prefer precise workspace names/IDs in prompts.
- For production-impacting operations (delete/deploy/remove permissions), confirm explicitly.
- For large jobs, ask for a **plan + telemetry + flow output**.
```
Trace end-to-end data lineage for the Revenue Dashboard
Show me what's impacted if I change the Bronze lakehouse schema
Analyze lineage from source system to final report
Find all items that depend on the CustomerDim table
```

---

## 🤖 AI & Advanced Features

### Copilot
```
Enable Copilot for the Analytics workspace
Analyze Copilot usage patterns — what are users asking most?
```

### GraphQL API
```
Create a GraphQL API exposing Lakehouse tables to external apps
Update GraphQL schema to add filtering on date range
Analyze GraphQL API request volume and latency
```

### Data Agent
```
Create a Data Agent for natural-language querying of the Sales model
Update Data Agent knowledge base with business glossary
Analyze Data Agent query accuracy and user satisfaction
```

### UDFs
```
Create a user-defined function for custom fiscal year calculation
Update UDF to handle null values gracefully
Analyze UDF usage across all notebooks
```

---

## 🔗 Multi-Step Workflows

### End-to-End Lakehouse Pipeline
```
Build a complete data platform: create Bronze, Silver, Gold lakehouses,
ETL notebooks for each layer, a daily pipeline, and configure
security roles — all in workspace ws-data-prod
```

### Workspace Governance Setup
```
Create workspace Finance-Prod with F64 capacity, set up admin and
viewer security roles, connect to Azure DevOps git repo, and create a
Dev-Test-Prod deployment pipeline
```

### Migration from Dev to Prod
```
Deploy the latest changes from Development to Production: sync the
git branch, run the deployment pipeline, and verify all items deployed
correctly
```

---

## 🔍 Analysis & Audit

```
Show me everything in workspace ws-analytics-001
Analyze capacity utilization across all workspaces for this month
List all failed pipeline runs in the last 7 days
Show data lineage for the Executive Dashboard
Audit who has admin access across all production workspaces
Compare item counts between Dev and Prod workspaces
```

---

## 🗑️ Cleanup & Deletion

```
Delete the deprecated staging lakehouse and its shortcuts
Remove the old test notebooks from the Dev workspace
Delete the unused deployment pipeline called "OldPipeline"
```

---

> **Tip:** You can combine multiple requests in a single prompt.
> The orchestrator will decompose them into separate steps automatically.
>
> **Tip:** After execution, check the agent's `sample_prompts.md` file
> to see the logged history — it helps the system learn from real usage!
