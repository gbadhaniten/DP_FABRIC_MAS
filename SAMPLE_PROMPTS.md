# 💡 SAMPLE PROMPTS — Fabric Multi-Agent System (Fabric-MAS)

> Master catalogue of sample prompts organised by use case.
> Use these as starting points — the system handles natural language, so
> feel free to rephrase in your own words.
> **Copilot-Native** — Just type these in GitHub Copilot Chat. No API key needed.

---

## 📂 Table of Contents
1. [Data Engineering](#-data-engineering)
2. [Data Integration & ETL](#-data-integration--etl)
3. [Analytics & Warehousing](#-analytics--warehousing)
4. [Data Modeling (NEW)](#-data-modeling)
5. [Real-Time Intelligence](#-real-time-intelligence)
6. [Reporting & Power BI](#-reporting--power-bi)
7. [Governance & Administration](#-governance--administration)
8. [AI & Advanced Features](#-ai--advanced-features)
9. [Multi-Step Workflows](#-multi-step-workflows)
10. [Analysis & Audit](#-analysis--audit)
11. [Cleanup & Deletion](#-cleanup--deletion)

---

## 🗄️ Data Engineering

### Lakehouse
```
Create a Bronze lakehouse for raw data ingestion in workspace ws-123
Create Bronze, Silver, and Gold lakehouses for a medallion architecture
Update the Gold lakehouse description to "Curated Analytics Layer"
Delete the deprecated staging lakehouse in workspace ws-old
Analyze tables and files in the Bronze lakehouse
```

### OneLake & Shortcuts
```
Create a OneLake shortcut to our ADLS Gen2 container at abfss://raw@storage.dfs.core.windows.net
List all shortcuts in the Bronze lakehouse
Delete the S3 shortcut that's no longer needed
Analyze OneLake storage usage across all lakehouses in the workspace
```

### Notebooks
```
Create an ETL notebook called TransformSales for Bronze to Silver processing
Create a PySpark notebook for data quality checks
Update the TransformSales notebook to use Spark 3.4 runtime
Analyze notebook execution history — show me failures from the last week
```

### Environments
```
Create a Spark environment with pandas, numpy, and scikit-learn
Update the ML environment to add tensorflow and pytorch
Analyze environment compute configuration and library versions
```

### Spark Jobs
```
Create a Spark job definition for daily sales aggregation
Update the Spark job to use 8 executors and 32GB memory
Analyze Spark job execution performance over the last month
```

---

## 🔄 Data Integration & ETL

### Data Pipelines
```
Create a pipeline called DailyETL with a notebook activity that runs TransformSales
Create a pipeline with Copy activity from SQL Server to Lakehouse, then run a notebook
Update the DailyETL pipeline to run every 6 hours instead of daily
Analyze pipeline run history — show failures and average duration
```

### Dataflows
```
Create a Dataflow Gen2 for customer data cleansing and deduplication
Update the CustomerDataflow to add a merge step with product dimension
Analyze dataflow refresh history and performance
```

### Copy Jobs
```
Create a copy job from Azure SQL Database to the Bronze lakehouse
Create a copy job from on-prem SQL Server to Fabric using gateway
Update the copy job column mapping for new schema changes
Analyze copy job throughput — how many rows per minute?
```

---

## 📊 Analytics & Warehousing

### Warehouse
```
Create a Synapse Warehouse called SalesWarehouse in workspace ws-analytics
Create warehouse with stored procedures for the reporting layer
Update warehouse with new views for the finance team
Analyze warehouse query performance — find the slowest queries
```

### SQL Database
```
Create a SQL Database for operational reporting
Update database schema with new customer dimension table
Analyze SQL database size, growth rate, and index usage
```

### Mirrored Database
```
Create a mirrored database from our Azure SQL production server
Create mirroring for Cosmos DB analytical store
Update mirroring configuration to include new tables
Analyze mirroring replication lag and sync status
```

### SQL Endpoints
```
Analyze SQL endpoint connection strings for all lakehouses
List all SQL endpoints and their auto-generated views
Check SQL endpoint availability and response times
```

---

## 🧩 Data Modeling

### Star Schema
```
Generate a star schema for sales analytics with Fact_Sales and dimensions for Date, Customer, Product, Store
Create a star schema model for inventory management
Build a dimensional model for HR analytics with employee and department dimensions
```

### Snowflake Schema
```
Generate a snowflake schema for e-commerce with normalized product hierarchy
Create a snowflake model for the finance domain with account and cost center hierarchies
```

### SCD (Slowly Changing Dimensions)
```
Create dimension tables with SCD Type 2 for customer address tracking
Generate a model with SCD Type 1 for product category (overwrite, no history)
Build Dim_Employee with SCD Type 2 tracking department changes
```

### Output Formats
```
Generate a sales star schema as SQL DDL for Fabric Warehouse
Create a product analytics model and output as TMDL
Generate a data model definition as JSON for review
```

### Update Guidelines
```
Update data modeling guidelines: use 'f_' prefix for facts and 'd_' for dimensions
Update the naming convention to use PascalCase for table names
Add a guideline: all date dimensions must include fiscal year columns
Show me the current data modeling guidelines
```

### Combined Workflows
```
Create a Gold lakehouse, generate a star schema for sales, and create a semantic model on top
Design a dimensional model for customer analytics, generate SQL, then create it in the warehouse
```

---

### KQL Queries
```
Create a KQL Queryset for anomaly detection on temperature readings
```

### Data Activator & Reflex
```
Create a Data Activator trigger when CPU exceeds 90%
Create a Reflex that sends an email when sales drop below threshold
Update Activator alert to include Teams notification
Analyze alert history — how many triggers in the last 24 hours?
```

---

## 📈 Reporting & Power BI

### Semantic Models
```
Create a semantic model from the Gold lakehouse tables
Create a composite model combining warehouse and lakehouse sources
Update semantic model with new DAX measures for YoY comparison
Analyze semantic model refresh performance and size
```

### Reports
```
Create a Power BI report from the Sales semantic model
Create a paginated report for monthly financial statements
Update report theme to corporate branding guidelines
Analyze report usage — who's viewing it and how often?
```

### Dashboards
```
Create a Power BI dashboard with pinned visuals from Sales report
Update dashboard to add a new real-time tile
Analyze dashboard data refresh schedule and staleness
```

### Apps
```
Create a Power BI app for the Finance team with curated content
Update app audience to include the Marketing group
Deploy the latest app update to all subscribers
Analyze app adoption metrics — installs, active users, engagement
```

---

## 🔐 Governance & Administration

### Workspace Management
```
Create a new workspace called DataPlatform-Prod
Create workspaces for Dev, Test, and Prod environments
Update workspace to assign F64 capacity
Analyze workspace item inventory — list everything with sizes
```

### Capacity
```
Assign F64 capacity to the production workspace
Update capacity from F32 to F64 for peak month-end processing
Analyze capacity utilization — are we being throttled?
Scale down capacity to F16 for the weekend
```

### Security
```
Create workspace role assignments: Admins=IT Team, Viewers=Business Users
Update security to add the DataEngineers group as Contributors
Analyze who has access to what in the workspace
Audit permissions for the sensitive Financial workspace
```

### Deployment Pipelines
```
Create a Dev → Test → Prod deployment pipeline
Deploy all items from Test stage to Production
Analyze deployment history — show rollbacks and failures
Compare Dev and Prod stages for configuration drift
```

### Git Integration
```
Connect workspace to our Azure DevOps repository
Sync workspace with the main branch
Analyze git sync status — are there conflicts?
Update git branch from feature/etl-update to main
```

### Domains
```
Create a domain called "Finance Analytics" and assign workspaces
Update domain endorsement to "Promoted" for the Gold workspace
```

### Lineage
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

### UDFs & AI Functions
```
Create a user-defined function for custom fiscal year calculation
Create an AI function that calls Azure OpenAI for text classification
Update UDF to handle null values gracefully
Analyze UDF usage across all notebooks
```

---

## 🔗 Multi-Step Workflows

### End-to-End Lakehouse Pipeline
```
Build a complete data platform: create Bronze, Silver, Gold lakehouses,
ETL notebooks for each layer, a daily pipeline, a semantic model,
and a Power BI report — all in workspace ws-data-prod
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
git branch, run the deployment pipeline, verify the semantic model
refresh, and check the report renders correctly
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
