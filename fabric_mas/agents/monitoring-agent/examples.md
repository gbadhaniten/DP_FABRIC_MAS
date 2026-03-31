# Monitoring Agent — Examples

## Example 1: Get Failed Jobs
**Prompt:** "Show me all failed jobs in workspace DIG_FAB_MULTIAGENT"
**Plan:**
```json
{
  "agents": ["monitoring"],
  "operation": "analyze",
  "params": {
    "workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3",
    "mode": "failed_jobs"
  }
}
```
**Result:** Scanned 12 schedulable items — 2 have recent failures.

---

## Example 2: Job History for a Pipeline
**Prompt:** "Show job history for pipeline PL_COPY_MDM_SECURITY_TO_MDM"
**Plan:**
```json
{
  "agents": ["monitoring"],
  "operation": "analyze",
  "params": {
    "workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3",
    "item_id": "1b89538e-6145-42dc-bd08-37d4084eda2b",
    "mode": "job_history"
  }
}
```
**Result:** Job history: 15 runs — 12 OK, 2 failed, 1 running.

---

## Example 3: Workspace Health Check
**Prompt:** "Is my workspace healthy?"
**Plan:**
```json
{
  "agents": ["monitoring"],
  "operation": "analyze",
  "params": {
    "workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3",
    "mode": "workspace_health"
  }
}
```
**Result:** Workspace 'DIG_FAB_MULTIAGENT': 28 items across 7 types.

---

## Example 4: Trigger Pipeline Run
**Prompt:** "Run pipeline PL_DAILY_LOAD now"
**Plan:**
```json
{
  "agents": ["monitoring"],
  "operation": "create",
  "params": {
    "workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3",
    "item_id": "1b89538e-6145-42dc-bd08-37d4084eda2b",
    "job_type": "Pipeline"
  }
}
```
**Result:** Job run triggered for item (type=Pipeline).

---

## Example 5: Capacity Info
**Prompt:** "What capacity is my workspace using?"
**Plan:**
```json
{
  "agents": ["monitoring"],
  "operation": "analyze",
  "params": {
    "workspace_id": "8952abd5-c851-4c8c-a6ba-2748519aebe3",
    "mode": "capacity"
  }
}
```
**Result:** Capacity 'FabDev_F64' (F64) in West Europe — state: Active.
