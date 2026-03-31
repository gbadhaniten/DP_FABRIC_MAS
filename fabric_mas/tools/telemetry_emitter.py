"""
fabric_mas/tools/telemetry_emitter.py
======================================
Drop this file into your fabric_mas/tools/ folder.
Import it in base_agent.py and orchestrator.py.
It emits every agent event to the local log server (http://localhost:7842/api/log).
If the server is not running, it fails silently (never blocks agent execution).

USAGE IN base_agent.py — add at top:
    from fabric_mas.tools.telemetry_emitter import emit_event, emit_job_start, emit_job_end

USAGE IN orchestrator.py — add at top:
    from fabric_mas.tools.telemetry_emitter import emit_event, emit_job_start, emit_job_end
"""

import json
import time
import threading
import urllib.request
import urllib.error
from datetime import datetime, timezone

LOG_SERVER = "http://localhost:7842/api/log"
ENABLED = True  # set to False to disable without removing imports

_job_start_times: dict = {}
_step_start_times: dict = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _post(payload: dict) -> None:
    """Fire-and-forget POST — never blocks, never raises."""
    if not ENABLED:
        return
    def _send():
        try:
            data = json.dumps(payload, default=str).encode()
            req = urllib.request.Request(
                LOG_SERVER,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=2):
                pass
        except Exception:
            pass  # server not running — silently skip
    threading.Thread(target=_send, daemon=True).start()


def emit_job_start(
    job_id: str,
    job_name: str,
    user_prompt: str,
    workspace: str = "",
) -> float:
    """Call at the start of every execute_task() / orchestrator job."""
    t = time.time()
    _job_start_times[job_id] = t
    _post({
        "event_type": "job_start",
        "timestamp": _now_iso(),
        "job_id": job_id,
        "job_name": job_name,
        "user_prompt": user_prompt,
        "workspace": workspace,
        "agent": "orchestrator",
        "operation": "job_start",
        "status": "running",
        "tokens": 0,
        "cli_command": "",
        "start_ms": 0,
        "duration_ms": 0,
        "detail": f"Job started: {job_name}",
    })
    return t


def emit_step_start(
    job_id: str,
    step_key: str,
) -> float:
    """Call immediately before an agent.execute() call."""
    t = time.time()
    _step_start_times[f"{job_id}:{step_key}"] = t
    return t


def emit_event(
    job_id: str,
    job_name: str,
    agent: str,
    operation: str,
    cli_command: str,
    status: str,               # "ok" | "fail" | "running" | "skipped"
    tokens: int = 0,
    detail: str = "",
    workspace: str = "",
    item_name: str = "",
    item_type: str = "",
    source_workspace: str = "",
    source_item: str = "",
    error_message: str = "",
    step_key: str = "",
) -> None:
    """
    Emit a single agent step event.
    Call AFTER every agent.execute() or CLI call returns.

    step_key: unique string per step — used to measure duration.
              Typically f"{agent}_{operation}_{item_name}".
    """
    now = time.time()
    job_start = _job_start_times.get(job_id, now)
    step_start = _step_start_times.pop(f"{job_id}:{step_key}", now)

    start_ms = round((step_start - job_start) * 1000)
    duration_ms = round((now - step_start) * 1000)

    _post({
        "event_type": "step",
        "timestamp": _now_iso(),
        "job_id": job_id,
        "job_name": job_name,
        "agent": agent,
        "operation": operation,
        "cli_command": cli_command,
        "status": status,
        "tokens": tokens,
        "detail": detail,
        "workspace": workspace,
        "item_name": item_name,
        "item_type": item_type,
        "source_workspace": source_workspace,
        "source_item": source_item,
        "error_message": error_message,
        "start_ms": start_ms,
        "duration_ms": duration_ms,
    })


def emit_job_end(
    job_id: str,
    job_name: str,
    status: str,               # "done" | "fail" | "partial"
    total_tokens: int = 0,
    summary: str = "",
) -> None:
    """Call at the end of every execute_task()."""
    now = time.time()
    job_start = _job_start_times.pop(job_id, now)
    total_ms = round((now - job_start) * 1000)

    _post({
        "event_type": "job_end",
        "timestamp": _now_iso(),
        "job_id": job_id,
        "job_name": job_name,
        "agent": "orchestrator",
        "operation": "job_end",
        "status": status,
        "tokens": total_tokens,
        "cli_command": "",
        "start_ms": 0,
        "duration_ms": total_ms,
        "detail": summary or f"Job {status} in {total_ms}ms, {total_tokens} tokens",
    })
