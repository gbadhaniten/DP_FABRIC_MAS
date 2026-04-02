# Fabric-MAS Workflows

> Detailed multi-agent workflow patterns for common Microsoft Fabric use cases.
> Each workflow shows the agent sequence, dependencies, and expected data flow.

---

## 1. Medallion Architecture Setup

**Goal:** Build a complete Bronze → Silver → Gold data lakehouse with ETL pipelines.

```
┌──────────────────┐
│ workspace-agent   │ ──▶ Create/validate workspace
└────────┬─────────┘
         ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ lakehouse-agent   │    │ lakehouse-agent   │    │ lakehouse-agent   │
│ CREATE "Bronze"   │    │ CREATE "Silver"   │    │ CREATE "Gold"     │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ shortcut-agent    │    │ shortcut-agent    │
│ Bronze→ADLS link  │    │ Cross-LH links   │
└────────┬─────────┘    └──────────────────┘
         ▼
┌──────────────────┐    ┌──────────────────┐
│ notebook-agent    │    │ notebook-agent    │
│ Bronze→Silver ETL │    │ Silver→Gold ETL   │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         ▼                       ▼
┌──────────────────────────────────────────┐
│ data-pipeline-agent                       │
│ CREATE DailyETL pipeline with schedule    │
└──────────────────────────────────────────┘
```

**Agent Sequence:**
1. `workspace-agent` → create or validate workspace
2. `lakehouse-agent` × 3 → create Bronze, Silver, Gold lakehouses (⚡ parallel)
3. `shortcut-agent` → create source data shortcut (ADLS, S3, etc.)
4. `notebook-agent` × 2 → create ETL notebooks per layer
5. `data-pipeline-agent` → create orchestration pipeline with schedule

---

## 2. Workspace Governance & Security

**Goal:** Set up a governed workspace with RBAC, git, CI/CD, and compliance.

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ workspace-agent   │    │ workspace-agent   │    │ workspace-agent   │
│ CREATE "Dev"      │    │ CREATE "Test"     │    │ CREATE "Prod"     │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         └───────────┬───────────┘───────────┬───────────┘
                     ▼                       ▼
         ┌──────────────────┐
         │ capacity-agent    │
         │ Assign F64        │
         └────────┬─────────┘
                  ▼                       ▼
         ┌──────────────────┐
         │ security-agent    │
         │ RBAC roles:       │
         │ Admin, Contrib,   │
         │ Viewer            │
         └────────┬─────────┘
                  ▼
         ┌──────────────────┐    ┌──────────────────┐
         │ git-integration-  │    │ deployment-       │
         │ agent             │    │ pipeline-agent    │
         │ Connect to DevOps │    │ Dev→Test→Prod     │
         └──────────────────┘    └──────────────────┘
```

**Agent Sequence:**
1. `workspace-agent` × 3 → create Dev, Test, Prod workspaces (parallel)
2. `capacity-agent` → assign capacity to production
3. `security-agent` → configure RBAC roles per workspace
4. `git-integration-agent` → connect workspace to git repository
5. `deployment-pipeline-agent` → create CI/CD pipeline across stages

---

## 3. Data Warehouse Analytics

**Goal:** Build a warehouse with SQL analytics and deploy through environments.

```
┌──────────────────┐
│ warehouse-agent   │ ──▶ CREATE warehouse from Gold lakehouse
└────────┬─────────┘
         ▼
┌──────────────────┐
│ sql-endpoint-     │ ──▶ CONFIGURE SQL endpoint for read access
│ agent             │
└────────┬─────────┘
         ▼
┌──────────────────┐    ┌──────────────────┐
│ data-modeling-    │    │ security-agent    │
│ agent             │    │ Configure RBAC    │
│ Star schema       │    │ for warehouse     │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         ▼                       ▼
┌──────────────────────────────────────────┐
│ deployment-pipeline-agent                 │
│ DEPLOY from Dev → Test → Prod             │
└──────────────────────────────────────────┘
```

**Agent Sequence:**
1. `warehouse-agent` → create warehouse and load data from Gold lakehouse
2. `sql-endpoint-agent` → configure SQL endpoint for downstream access
3. `data-modeling-agent` → generate star schema in warehouse
4. `security-agent` → assign RBAC roles for warehouse consumers
5. `deployment-pipeline-agent` → promote through Dev → Test → Prod

---

## 4. Data Integration from External Sources

**Goal:** Ingest data from external databases into Fabric.

```
┌──────────────────┐    ┌──────────────────┐
│ copy-job-agent    │    │ mirrored-db-agent │
│ Copy from SQL     │    │ Mirror from       │
│ Server / S3       │    │ Cosmos DB         │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         ▼                       ▼
┌──────────────────────────────────────────┐
│ lakehouse-agent                           │
│ Data lands in Bronze lakehouse            │
└────────┬─────────────────────────────────┘
         ▼
┌──────────────────┐
│ notebook-agent    │
│ PySpark cleansing │
│ & transformation  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ data-pipeline-agent                       │
│ Orchestrate: Copy → Transform → Load      │
└──────────────────────────────────────────┘
```

**Agent Sequence:**
1. `copy-job-agent` / `mirrored-db-agent` → ingest from external sources
2. `lakehouse-agent` → raw data lands in Bronze
3. `notebook-agent` → transform and cleanse with PySpark
4. `data-pipeline-agent` → orchestrate the full ETL flow

---

## 5. AI & Advanced Analytics

**Goal:** Set up AI-powered features and natural-language querying.

```
┌──────────────────┐
│ graphql-api-agent │ ──▶ Expose lakehouse tables via GraphQL
└────────┬─────────┘
         ▼
┌──────────────────┐    ┌──────────────────┐
│ data-agent-agent  │    │ copilot-agent     │
│ Natural language   │    │ Enable Copilot    │
│ query interface   │    │ for workspace     │
└──────────────────┘    └──────────────────┘
```

**Agent Sequence:**
1. `graphql-api-agent` → create API layer over data
2. `data-agent-agent` → create natural-language query agent
3. `copilot-agent` → enable Copilot features

---

## 6. Audit & Compliance Analysis

**Goal:** Inspect workspace health and lineage.

```
┌──────────────────┐
│ workspace-agent   │ ──▶ ANALYZE all items in workspace
└────────┬─────────┘
         ▼
┌──────────────────┐
│ lineage-agent     │
│ Trace data flow   │
│ end-to-end        │
└──────────────────┘
```

**Agent Sequence:**
1. `workspace-agent` → list and analyse all items
2. `lineage-agent` → trace data flow from source to report
