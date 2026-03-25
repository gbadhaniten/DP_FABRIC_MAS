# Data Modeling Agent — Examples & Learned Patterns

## Few-Shot Examples

| # | User Request | Operation | Output |
|---|---|---|---|
| 1 | "Create a star schema for sales analytics" | create | Star schema with Fact_Sales + Dim_Date, Dim_Customer, Dim_Product, Dim_Store |
| 2 | "Generate a snowflake model for HR data" | create | Snowflake schema with Fact_Employee_Activity + normalized dimensions |
| 3 | "Build dimension tables with SCD Type 2 for customer tracking" | create | Dim_Customer with surrogate_key, effective_date, expiry_date, is_current |
| 4 | "Show me the current data modeling guidelines" | analyze | Returns instructions.md contents with naming conventions and SCD rules |
| 5 | "Update naming convention: use prefix 'f_' for facts and 'd_' for dims" | update | Updates instructions.md with custom naming convention |
| 6 | "Create a sales model with SQL output for Fabric Warehouse" | create | SQL DDL with CREATE TABLE statements for all tables |
| 7 | "Generate TMDL for a product analytics model" | create | TMDL file with tables, columns, measures, and relationships |
| 8 | "Design an inventory snapshot model with monthly grain" | create | Periodic snapshot fact table + inventory dimensions |

## Multi-Step Workflow Examples

### Medallion + Dimensional Model
```
Prompt: "Create a medallion architecture and then build a star schema
         on the Gold layer for sales analytics"

Steps:
  1. lakehouse-agent → create Bronze lakehouse
  2. lakehouse-agent → create Silver lakehouse
  3. lakehouse-agent → create Gold lakehouse
  4. data-modeling-agent → create Sales star schema (targeting Gold)
  5. semantic-model-agent → create Sales semantic model
```

### Custom Guidelines + Model Generation
```
Prompt: "Update our naming to use 'f_' for facts and 'd_' for dims,
         then generate a customer analytics model"

Steps:
  1. data-modeling-agent → update guidelines (naming convention)
  2. data-modeling-agent → create customer analytics star schema
```

---

## Execution Log (Auto-Appended Below)
