# Monitoring Agent — Known Issues

## Authentication expired
- **Pattern:** `InteractionRequired` / `Authentication expired`
- **Cause:** Cached Fabric token expired or wrong account selected
- **Workaround:** Re-authenticate with the `_AZR` account and retry once
- **Auto-apply:** true

## Jobs endpoint unavailable for item type
- **Pattern:** `404` or `OperationNotSupported` when querying `/jobs/instances`
- **Cause:** Some Fabric item types do not expose schedulable jobs
- **Workaround:** Skip the item during workspace-wide failure scans
- **Auto-apply:** true

## Capacity not assigned
- **Pattern:** Missing `capacityId` on workspace
- **Cause:** Workspace is in shared/trial mode
- **Workaround:** Return informational status instead of error
- **Auto-apply:** true

## Empty history
- **Pattern:** Successful response with no job instances
- **Cause:** Item has not been run yet
- **Workaround:** Return a healthy empty result (`0 runs`) rather than failure
- **Auto-apply:** true# Monitoring Agent — Known Issues

## Issue 1: Job Instances API Returns 404 for Non-Schedulable Items
- **Error:** `404 Not Found` when querying job instances for items that don't support scheduling
- **Affected types:** Shortcut, Domain, Capacity, Security roles
- **Workaround:** Only query schedulable types: DataPipeline, Notebook, SemanticModel,
  DataflowGen2, SparkJobDefinition, Lakehouse, Warehouse
- **Auto-apply:** true — the `_get_failed_jobs()` method filters by schedulable types

## Issue 2: Large Workspaces Slow on Failed-Jobs Scan
- **Symptom:** Workspace with 50+ schedulable items takes >30 seconds for failed_jobs scan
- **Cause:** Sequential REST calls per item (one GET per item)
- **Workaround:** None currently — future enhancement: parallel requests
- **Auto-apply:** false

## Issue 3: Capacity API Requires Admin Permissions
- **Error:** `403 Forbidden` when querying `/capacities/{id}`
- **Cause:** Capacity read access requires Capacity Admin or Fabric Admin role
- **Workaround:** Inform user they need elevated permissions
- **Auto-apply:** false

## Issue 4: Job Instance Status Values
- **Note:** Fabric API returns these status values:
  - `Completed` — succeeded
  - `Failed` — failed with error
  - `InProgress` — currently running
  - `Cancelled` — user-cancelled
  - `Deduped` — skipped due to another instance running
- **Not a bug:** but important for correct counting
