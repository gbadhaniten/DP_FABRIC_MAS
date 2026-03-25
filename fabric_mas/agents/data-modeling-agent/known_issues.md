# Data Modeling Agent — Known Issues

## Issue 1: SQL Dialect Differences
**Problem:** Generated SQL DDL may use T-SQL syntax (IDENTITY, GETDATE) that isn't
compatible with Spark SQL in Lakehouse notebooks.
**Workaround:** Use `output_format="json"` and generate Spark-compatible DDL manually,
or target a Warehouse instead of a Lakehouse SQL Endpoint for DDL execution.

## Issue 2: TMDL Output is Skeleton Only
**Problem:** The generated TMDL is a structural skeleton — it does not include
data source definitions, partitions, or Power Query M expressions.
**Workaround:** Use the TMDL output as a starting point and fill in data source
bindings in Power BI Desktop or Tabular Editor.

## Issue 3: Complex Snowflake Schemas
**Problem:** Deeply normalized snowflake schemas with 3+ levels of dimension
hierarchy may not render all intermediate tables.
**Workaround:** Generate the model in `json` format, manually add intermediate
tables, then regenerate SQL from the updated JSON.

## Issue 4: Custom Naming Convention Persistence
**Problem:** Custom naming conventions added via `update guidelines` are stored
in instructions.md text but not yet parsed back as structured config.
**Workaround:** The agent uses default naming prefixes (Fact_, Dim_). After updating
guidelines, manually verify generated output matches your conventions.

## Issue 5: No Physical Table Creation
**Problem:** This agent generates model *definitions* (DDL/TMDL/JSON) but does not
create physical tables in Fabric. It is a design-time agent.
**Workaround:** Use the generated SQL with the `warehouse-agent` or execute it
directly in a Fabric Warehouse/SQL Endpoint.
