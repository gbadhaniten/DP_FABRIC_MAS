# 📏 Naming Convention — Microsoft Fabric Resources
# ===================================================
# This file is the **single source of truth** for all Fabric item naming.
# Every agent in Fabric-MAS checks this document before creating any resource.
#
# HOW IT WORKS:
#   - BaseAgent loads this file at startup
#   - On every `create` operation, the agent validates `display_name` against
#     the pattern defined here for that item type
#   - If the name doesn't match, the agent auto-corrects it OR rejects with
#     a clear error message showing the expected pattern
#
# TO CUSTOMISE: Edit the patterns below. Changes take effect immediately
# on the next MCP server call (no restart needed — the file is re-read
# each time an agent is instantiated).
# ===================================================

---

## General Rules

| Rule | Convention | Example |
|------|-----------|---------|
| **Case** | UPPER_SNAKE_CASE for all items | `LH_SALES_BRONZE` |
| **Separator** | Underscore `_` (no spaces, no hyphens) | `WH_FINANCE_GOLD` |
| **Max Length** | 80 characters | — |
| **Allowed Chars** | `A-Z`, `0-9`, `_` only | — |
| **No Trailing/Leading `_`** | Strip before validation | — |
| **Environment Suffix** | Optional — append `_DEV`, `_UAT`, `_PRD` when applicable | `LH_SALES_BRONZE_DEV` |

---

## Item Type Prefixes

Every Fabric item name **MUST** start with a prefix that identifies its type.

| Item Type | Prefix | Pattern | Example |
|-----------|--------|---------|---------|
| **Workspace** | `WKS_` | `WKS_<DOMAIN>_<PURPOSE>[_ENV]` | `WKS_DP_DATA_AGENTS_DEV` |
| **Lakehouse** | `LH_` | `LH_<DOMAIN/SOURCE>_<LAYER>[_ENV]` | `LH_SALES_BRONZE` |
| **Warehouse** | `WH_` | `WH_<DOMAIN>_<LAYER>[_ENV]` | `WH_FINANCE_GOLD` |
| **Notebook** | `NB_` | `NB_<PURPOSE>_<DETAIL>` | `NB_ETL_SALES_LOAD` |
| **Data Pipeline** | `PL_` | `PL_<PURPOSE>_<DETAIL>` | `PL_DAILY_SALES_INGESTION` |
| **Dataflow Gen2** | `DF_` | `DF_<PURPOSE>_<DETAIL>` | `DF_TRANSFORM_CUSTOMER` |
| **Copy Job** | `CJ_` | `CJ_<SOURCE>_TO_<TARGET>` | `CJ_SAP_TO_BRONZE` |
| **Spark Job Definition** | `SJ_` | `SJ_<PURPOSE>_<DETAIL>` | `SJ_AGGREGATE_MONTHLY` |
| **Semantic Model** | `SM_` | `SM_<DOMAIN>_<PURPOSE>` | `SM_SALES_REPORTING` |
| **Report** | `RPT_` | `RPT_<DOMAIN>_<PURPOSE>` | `RPT_FINANCE_MONTHLY` |
| **Dashboard** | `DSH_` | `DSH_<DOMAIN>_<PURPOSE>` | `DSH_EXECUTIVE_KPI` |
| **Power BI App** | `APP_` | `APP_<DOMAIN>_<PURPOSE>` | `APP_HR_ANALYTICS` |
| **SQL Database** | `SQLDB_` | `SQLDB_<DOMAIN>_<PURPOSE>` | `SQLDB_MDM_MASTER` |
| **SQL Analytics Endpoint** | `SQLE_` | `SQLE_<DOMAIN>_<PURPOSE>` | `SQLE_SALES_ANALYTICS` |
| **Mirrored Database** | `MDB_` | `MDB_<SOURCE>_<PURPOSE>` | `MDB_ORACLE_FINANCE` |
| **KQL Queryset** | `KQLQS_` | `KQLQS_<DOMAIN>_<PURPOSE>` | `KQLQS_IOT_ALERTS` |
| **Data Activator / Reflex** | `RFX_` | `RFX_<DOMAIN>_<PURPOSE>` | `RFX_ALERT_THRESHOLD` |
| **Deployment Pipeline** | `DPL_` | `DPL_<PURPOSE>` | `DPL_CICD_SALES` |
| **Domain** | `DOM_` | `DOM_<NAME>` | `DOM_FINANCE` |
| **Shortcut** | `SC_` | `SC_<SOURCE>_<TARGET>` | `SC_ADLS_RAW_SALES` |
| **GraphQL API** | `GQL_` | `GQL_<DOMAIN>_<PURPOSE>` | `GQL_CUSTOMER_API` |
| **Monitoring** | `MON_` | `MON_<PURPOSE>_<DETAIL>` | `MON_PLATFORM_HEALTH` |
| **Variable Library** | `VL_` | `VL_<PURPOSE>` | `VL_CONFIG_PARAMS` |
| **Task Flow** | `TF_` | `TF_<PURPOSE>` | `TF_DAILY_ORCHESTRATION` |
| **Map Visual** | `MAP_` | `MAP_<DOMAIN>_<PURPOSE>` | `MAP_GEO_SALES` |
| **Data Agent** | `DA_` | `DA_<DOMAIN>_<PURPOSE>` | `DA_SALES_COPILOT` |
| **AI Functions** | `AIF_` | `AIF_<PURPOSE>` | `AIF_SENTIMENT_ANALYSIS` |
| **User Data Functions** | `UDF_` | `UDF_<PURPOSE>` | `UDF_PARSE_ADDRESS` |
| **OneLake** | `OL_` | `OL_<PURPOSE>` | `OL_CENTRAL_STORE` |
| **Git Integration** | `GIT_` | `GIT_<REPO>_<BRANCH>` | `GIT_FABRIC_MAS_MAIN` |
| **Capacity** | `CAP_` | `CAP_<REGION>_<SIZE>` | `CAP_WESTEUROPE_F64` |
| **Security** | `SEC_` | `SEC_<PURPOSE>` | `SEC_ROW_LEVEL_SALES` |

---

## Layer Abbreviations (for Medallion Architecture)

| Layer | Abbreviation | Description |
|-------|-------------|-------------|
| Raw / Landing | `RAW` | Untransformed source data |
| Bronze | `BRONZE` | Raw data in Delta format |
| Silver | `SILVER` | Cleansed, conformed, deduplicated |
| Gold | `GOLD` | Business-ready aggregates / models |
| Platinum / Serving | `SERVING` | Curated for specific consumers |
| Staging | `STG` | Temporary staging area |
| Archive | `ARCH` | Historical / cold storage |

---

## Environment Suffixes

| Environment | Suffix | Usage |
|------------|--------|-------|
| Development | `_DEV` | Dev workspace items |
| Testing / QA | `_UAT` | User acceptance testing |
| Pre-production | `_PRE` | Pre-production / staging |
| Production | `_PRD` | Production |
| Sandbox | `_SBX` | Experimentation |

---

## Domain Abbreviations (Common)

| Domain | Abbreviation |
|--------|-------------|
| Data Platform | `DP` |
| Finance | `FIN` |
| Human Resources | `HR` |
| Sales | `SALES` |
| Marketing | `MKT` |
| Supply Chain | `SCM` |
| Operations | `OPS` |
| IT / Technology | `IT` |
| Master Data Management | `MDM` |
| Customer | `CUST` |
| Product | `PROD` |
| IoT / Telemetry | `IOT` |

> **Note:** Add your own domain abbreviations as needed.

---

## Examples — Full Naming

```
Workspace:      WKS_DP_DATA_PLATFORM_DEV
Lakehouse:      LH_SALES_BRONZE
Lakehouse:      LH_MDM_EBX_GOLD_PRD
Warehouse:      WH_FIN_GOLD
Notebook:       NB_ETL_SALES_DAILY_LOAD
Pipeline:       PL_INGESTION_SAP_SALES
Dataflow:       DF_TRANSFORM_CUSTOMER_DIM
Semantic Model: SM_SALES_MONTHLY_REPORTING
Report:         RPT_FIN_PNL_MONTHLY
Dashboard:      DSH_EXEC_KPI_OVERVIEW
```

---

## Validation Rules (Used by BaseAgent)

```yaml
# This section is machine-readable — BaseAgent parses it for validation.
# Format: ITEM_TYPE: PREFIX
validation:
  Lakehouse: "LH_"
  Warehouse: "WH_"
  Notebook: "NB_"
  DataPipeline: "PL_"
  DataflowGen2: "DF_"
  CopyJob: "CJ_"
  SparkJobDefinition: "SJ_"
  SemanticModel: "SM_"
  Report: "RPT_"
  Dashboard: "DSH_"
  PowerBIApp: "APP_"
  SQLDatabase: "SQLDB_"
  SQLAnalyticsEndpoint: "SQLE_"
  MirroredDatabase: "MDB_"
  KQLQueryset: "KQLQS_"
  Reflex: "RFX_"
  DataActivator: "RFX_"
  DeploymentPipeline: "DPL_"
  Domain: "DOM_"
  Shortcut: "SC_"
  GraphQLApi: "GQL_"
  Monitoring: "MON_"
  VariableLibrary: "VL_"
  TaskFlow: "TF_"
  MapVisual: "MAP_"
  DataAgent: "DA_"
  AIFunctions: "AIF_"
  UserDataFunctions: "UDF_"
  OneLake: "OL_"
  GitIntegration: "GIT_"
  Capacity: "CAP_"
  Security: "SEC_"
  Workspace: "WKS_"
```

---

## How Agents Use This File

1. **On startup** → `BaseAgent` loads `Naming_Convention.md` from the project root
2. **On `create`** → `validate_naming()` checks `display_name` against the rules:
   - Has correct prefix for the item type?
   - Uses UPPER_SNAKE_CASE?
   - Only allowed characters?
   - Within max length?
3. **If invalid** → Agent returns a warning with the expected pattern and a suggested corrected name
4. **If valid** → Proceeds with creation

---

*Last updated: 2026-03-30*
