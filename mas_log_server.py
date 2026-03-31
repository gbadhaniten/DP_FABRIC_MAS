"""
Fabric-MAS Live Log Server
==========================
Run this in a terminal alongside VS Code:
    python mas_log_server.py

It starts a lightweight HTTP server on port 7842.
The browser dashboard polls /api/events every 5 seconds.
The VS Code agent writes events via POST /api/log.
A CSV file (mas_activity_log.csv) is also maintained.

All events are stored in memory + CSV. No database needed.
"""

import http.server
import json
import csv
import os
import time
import threading
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

LOG_FILE = "mas_activity_log.csv"
PORT = 7842
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
}

# ── In-memory store ─────────────────────────────────────────────────────────
store = {
    "events": [],      # all individual agent events
    "jobs": {},        # job_id → job summary
    "session_start": datetime.now(timezone.utc).isoformat(),
    "total_tokens": 0,
}
store_lock = threading.Lock()

CSV_COLUMNS = [
    "timestamp", "job_id", "job_name", "agent", "operation",
    "cli_command", "start_ms", "duration_ms", "tokens",
    "status", "detail", "workspace", "item_name", "item_type",
    "source_workspace", "source_item", "error_message"
]

def ensure_csv():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()

def append_csv(row: dict):
    ensure_csv()
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writerow({col: row.get(col, "") for col in CSV_COLUMNS})

def append_event(event: dict):
    """Add an event to memory store and CSV."""
    with store_lock:
        event["seq"] = len(store["events"]) + 1
        event["received_at"] = datetime.now(timezone.utc).isoformat()
        store["events"].append(event)
        store["total_tokens"] += int(event.get("tokens", 0))

        # Update job summary
        jid = event.get("job_id", "unknown")
        if jid not in store["jobs"]:
            store["jobs"][jid] = {
                "job_id": jid,
                "job_name": event.get("job_name", jid),
                "status": "running",
                "started_at": event.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "agents_used": [],
                "total_tokens": 0,
                "total_steps": 0,
                "steps": [],
                "workspace": event.get("workspace", ""),
                "user_prompt": event.get("user_prompt", ""),
            }
        job = store["jobs"][jid]
        agent = event.get("agent", "unknown")
        if agent not in job["agents_used"]:
            job["agents_used"].append(agent)
        job["total_tokens"] += int(event.get("tokens", 0))
        job["total_steps"] += 1
        job["steps"].append(event)
        if event.get("status") in ("job_complete", "done"):
            job["status"] = "done"
            job["ended_at"] = event.get("timestamp", datetime.now(timezone.utc).isoformat())
        elif event.get("status") == "fail":
            job["status"] = "failed"

    append_csv(event)


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress default access log

    def send_json(self, data, code=200):
        body = json.dumps(data, default=str).encode()
        self.send_response(code)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == "/api/events":
            since = int(qs.get("since", [0])[0])
            with store_lock:
                events = store["events"][since:]
                jobs = list(store["jobs"].values())
                payload = {
                    "events": events,
                    "jobs": jobs,
                    "total_tokens": store["total_tokens"],
                    "session_start": store["session_start"],
                    "total_event_count": len(store["events"]),
                }
            self.send_json(payload)

        elif parsed.path == "/api/job":
            jid = qs.get("id", [""])[0]
            with store_lock:
                job = store["jobs"].get(jid)
            if job:
                self.send_json(job)
            else:
                self.send_json({"error": "job not found"}, 404)

        elif parsed.path == "/api/csv":
            # Return CSV as text
            try:
                with open(LOG_FILE, "r") as f:
                    content = f.read()
            except FileNotFoundError:
                content = ",".join(CSV_COLUMNS) + "\n"
            body = content.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", "attachment; filename=mas_activity_log.csv")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path == "/api/status":
            with store_lock:
                self.send_json({
                    "server": "fabric-mas-log-server",
                    "version": "1.0",
                    "port": PORT,
                    "total_events": len(store["events"]),
                    "total_jobs": len(store["jobs"]),
                    "total_tokens": store["total_tokens"],
                    "session_start": store["session_start"],
                    "csv_file": LOG_FILE,
                })
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/log":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                payload = json.loads(body)
                # Accept single event or batch
                if isinstance(payload, list):
                    for ev in payload:
                        append_event(ev)
                    self.send_json({"ok": True, "count": len(payload)})
                else:
                    append_event(payload)
                    self.send_json({"ok": True, "seq": payload.get("seq")})
            except json.JSONDecodeError as e:
                self.send_json({"error": str(e)}, 400)

        elif parsed.path == "/api/clear":
            with store_lock:
                store["events"].clear()
                store["jobs"].clear()
                store["total_tokens"] = 0
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
            self.send_json({"ok": True, "message": "session cleared"})

        else:
            self.send_json({"error": "not found"}, 404)


if __name__ == "__main__":
    ensure_csv()
    server = http.server.ThreadingHTTPServer(("", PORT), Handler)
    print(f"")
    print(f"  Fabric-MAS Log Server running on http://localhost:{PORT}")
    print(f"  Dashboard polls: GET /api/events")
    print(f"  VS Code agent posts: POST /api/log")
    print(f"  CSV log: {os.path.abspath(LOG_FILE)}")
    print(f"  Press Ctrl+C to stop")
    print(f"")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
