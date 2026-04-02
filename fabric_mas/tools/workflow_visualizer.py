"""
workflow_visualizer.py — Visual Agent Workflow GUI
====================================================
Renders a live visual workflow showing which agents are invoked,
their status, and the data-flow graph when a user query is processed.

Outputs:
  1. Rich terminal — live-updating panel with agent flow
  2. HTML file     — static export for sharing / embedding

Usage:
    from fabric_mas.tools.workflow_visualizer import WorkflowVisualizer
    viz = WorkflowVisualizer()
    viz.render_plan(plan, results)       # Rich terminal
    viz.export_html(plan, results, path) # HTML file
"""

from __future__ import annotations

import html
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from fabric_mas.core.orchestrator import ExecutionPlan, TaskStep
    from fabric_mas.core.base_agent import AgentResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent status colours / icons
# ---------------------------------------------------------------------------
STATUS_ICONS = {
    "pending":    ("⏳", "#888888", "Pending"),
    "running":    ("🔄", "#3498db", "Running"),
    "success":    ("✅", "#2ecc71", "Success"),
    "failed":     ("❌", "#e74c3c", "Failed"),
    "skipped":    ("⏭️",  "#f39c12", "Skipped"),
}

CATEGORY_COLORS = {
    "data_engineering":   "#1abc9c",
    "data_integration":   "#2ecc71",
    "analytics":          "#3498db",
    "realtime":           "#9b59b6",
    "governance":         "#e74c3c",
    "ai_advanced":        "#f1c40f",
    "orchestrator":       "#ecf0f1",
}


def _agent_category(agent_key: str) -> str:
    """Guess the category from the agent key for colour coding."""
    de = {"onelake", "lakehouse", "shortcut", "notebook", "spark_job"}
    di = {"data_pipeline", "copy_job", "adf", "data_wrangler"}
    an = {"warehouse", "sql_endpoint", "sql_database", "mirrored_db"}
    rt = {"kql_queryset", "data_activator"}
    ai = {"data_modeling", "data_agent", "copilot", "graphql_api", "udf"}
    go = {"workspace", "capacity", "deployment_pipeline", "git_integration",
          "lineage", "monitoring", "variable_library", "security"}
    k = agent_key.lower().replace("-", "_")
    if k in de: return "data_engineering"
    if k in di: return "data_integration"
    if k in an: return "analytics"
    if k in rt: return "realtime"
    if k in ai: return "ai_advanced"
    if k in go: return "governance"
    if k == "orchestrator": return "orchestrator"
    return "ai_advanced"


# ---------------------------------------------------------------------------
# Rich terminal rendering
# ---------------------------------------------------------------------------
class WorkflowVisualizer:
    """
    Renders execution plans as visual agent-flow diagrams.
    - Terminal: Rich panels with box-drawing connectors
    - HTML: Self-contained file with CSS animations
    """

    # ── Terminal (Rich) ──────────────────────────────────────────────

    def render_plan(
        self,
        plan: "ExecutionPlan",
        results: Optional[List["AgentResult"]] = None,
    ) -> str:
        """
        Render a plan as a Rich-compatible terminal string.
        Also returns the string for logging purposes.
        """
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table
            from rich.text import Text
            from rich.tree import Tree
            from rich import box
            return self._render_rich(plan, results)
        except ImportError:
            logger.info("Rich not installed — falling back to plain text")
            return self._render_plain(plan, results)

    def _render_rich(
        self,
        plan: "ExecutionPlan",
        results: Optional[List["AgentResult"]] = None,
    ) -> str:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text
        from rich.tree import Tree
        from rich import box
        import io

        console = Console(file=io.StringIO(), force_terminal=True, width=100)

        # Header
        console.print()
        console.print(
            Panel(
                f"[bold white]🧠 FABRIC-MAS WORKFLOW[/]\n"
                f"[dim]{plan.prompt}[/]",
                border_style="cyan",
                box=box.DOUBLE,
                width=96,
            )
        )

        # Build the flow tree
        tree = Tree(
            "🧠 [bold cyan]Orchestrator[/] receives prompt",
            guide_style="cyan",
        )
        planner_node = tree.add("📋 [bold yellow]LLM Planner[/] → JSON execution plan")

        for i, step in enumerate(plan.steps):
            status = "pending"
            result_msg = ""
            if results and i < len(results):
                r = results[i]
                status = "success" if r.success else "failed"
                result_msg = r.message[:60] if r.message else ""

            icon, color, label = STATUS_ICONS[status]
            cat = _agent_category(step.agent_key)
            cat_color = CATEGORY_COLORS.get(cat, "#cccccc")

            step_label = (
                f"{icon} [bold]Step {step.step_number}[/] → "
                f"[bold {cat_color}]{step.agent_key}[/]"
                f".[{color}]{step.operation}[/]"
            )
            step_node = planner_node.add(step_label)
            if step.description:
                step_node.add(f"[dim]{step.description}[/]")
            if result_msg:
                step_node.add(f"[{color}]{result_msg}[/]")

        console.print(tree)
        console.print()

        # Summary table
        if results:
            table = Table(
                title="📊 Execution Summary",
                box=box.ROUNDED,
                show_lines=True,
                title_style="bold",
                width=96,
            )
            table.add_column("Step", style="bold", width=6, justify="center")
            table.add_column("Agent", width=22)
            table.add_column("Operation", width=10)
            table.add_column("Status", width=10, justify="center")
            table.add_column("Result", width=42)

            for i, step in enumerate(plan.steps):
                r = results[i] if i < len(results) else None
                if r:
                    icon = "✅" if r.success else "❌"
                    style = "green" if r.success else "red"
                    msg = (r.message[:40] + "…") if r.message and len(r.message) > 40 else (r.message or "")
                else:
                    icon, style, msg = "⏳", "dim", "pending"

                table.add_row(
                    str(step.step_number),
                    step.agent_key,
                    step.operation,
                    f"[{style}]{icon}[/]",
                    f"[{style}]{msg}[/]",
                )

            console.print(table)

            ok = sum(1 for r in results if r.success)
            fail = len(results) - ok
            overall = "[bold green]ALL PASSED ✅[/]" if fail == 0 else f"[bold red]{fail} FAILED ❌[/]"
            console.print(f"\n  Total: {len(results)} steps | Passed: {ok} | Failed: {fail} | {overall}\n")

        output = console.file.getvalue()
        # Also print to real terminal
        real_console = Console(width=100)
        real_console.print(output)
        return output

    def _render_plain(
        self,
        plan: "ExecutionPlan",
        results: Optional[List["AgentResult"]] = None,
    ) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append("🧠 FABRIC-MAS WORKFLOW")
        lines.append(f"   Prompt: {plan.prompt}")
        lines.append("=" * 70)
        lines.append("")
        lines.append("  🧠 Orchestrator receives prompt")
        lines.append("  │")
        lines.append("  └─ 📋 LLM Planner → JSON execution plan")

        for i, step in enumerate(plan.steps):
            status = "⏳"
            result_msg = ""
            if results and i < len(results):
                r = results[i]
                status = "✅" if r.success else "❌"
                result_msg = f" → {r.message[:50]}" if r.message else ""

            connector = "├" if i < len(plan.steps) - 1 else "└"
            lines.append(f"     {connector}── {status} Step {step.step_number}: "
                         f"{step.agent_key}.{step.operation}{result_msg}")
            if step.description:
                pad = "│" if i < len(plan.steps) - 1 else " "
                lines.append(f"     {pad}      {step.description}")

        lines.append("")
        if results:
            ok = sum(1 for r in results if r.success)
            lines.append(f"  Summary: {ok}/{len(results)} succeeded")
        lines.append("=" * 70)

        output = "\n".join(lines)
        print(output)
        return output

    # ── HTML export ──────────────────────────────────────────────────

    def export_html(
        self,
        plan: "ExecutionPlan",
        results: Optional[List["AgentResult"]] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate a self-contained HTML file with an animated agent workflow.
        Returns the file path.
        """
        if output_path is None:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_path = str(
                Path(__file__).resolve().parent.parent.parent
                / "workflow_output"
                / f"workflow_{ts}.html"
            )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        steps_html = self._build_steps_html(plan, results)
        summary_html = self._build_summary_html(plan, results)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fabric-MAS Workflow</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', -apple-system, sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    padding: 2rem;
    min-height: 100vh;
  }}
  .header {{
    background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 2rem;
  }}
  .header h1 {{
    color: #58a6ff;
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
  }}
  .header .prompt {{
    color: #8b949e;
    font-style: italic;
    font-size: 0.95rem;
  }}
  .flow-container {{
    position: relative;
    padding-left: 3rem;
  }}
  .flow-line {{
    position: absolute;
    left: 1.5rem;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #30363d;
  }}
  .node {{
    position: relative;
    margin-bottom: 1.5rem;
    animation: slideIn 0.5s ease-out forwards;
    opacity: 0;
    transform: translateX(-20px);
  }}
  .node:nth-child(1) {{ animation-delay: 0.1s; }}
  .node:nth-child(2) {{ animation-delay: 0.3s; }}
  .node:nth-child(3) {{ animation-delay: 0.5s; }}
  .node:nth-child(4) {{ animation-delay: 0.7s; }}
  .node:nth-child(5) {{ animation-delay: 0.9s; }}
  .node:nth-child(6) {{ animation-delay: 1.1s; }}
  .node:nth-child(7) {{ animation-delay: 1.3s; }}
  .node:nth-child(8) {{ animation-delay: 1.5s; }}
  .node:nth-child(9) {{ animation-delay: 1.7s; }}
  .node:nth-child(10) {{ animation-delay: 1.9s; }}
  @keyframes slideIn {{
    to {{ opacity: 1; transform: translateX(0); }}
  }}
  .node-dot {{
    position: absolute;
    left: -2.15rem;
    top: 1rem;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    border: 2px solid #0d1117;
    z-index: 1;
  }}
  .node-dot.success {{ background: #2ecc71; box-shadow: 0 0 8px #2ecc7188; }}
  .node-dot.failed  {{ background: #e74c3c; box-shadow: 0 0 8px #e74c3c88; }}
  .node-dot.pending {{ background: #888; }}
  .node-dot.orchestrator {{ background: #58a6ff; box-shadow: 0 0 8px #58a6ff88; }}
  .node-card {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    transition: border-color 0.2s, transform 0.2s;
  }}
  .node-card:hover {{
    border-color: #58a6ff;
    transform: translateX(4px);
  }}
  .node-card.success {{ border-left: 3px solid #2ecc71; }}
  .node-card.failed  {{ border-left: 3px solid #e74c3c; }}
  .node-card.pending {{ border-left: 3px solid #888; }}
  .node-card.orch    {{ border-left: 3px solid #58a6ff; }}
  .node-title {{
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.3rem;
  }}
  .node-title .step-num {{ color: #8b949e; }}
  .node-title .agent {{ color: #58a6ff; }}
  .node-title .op {{ color: #f0883e; }}
  .node-desc {{ color: #8b949e; font-size: 0.85rem; margin-bottom: 0.3rem; }}
  .node-result {{ font-size: 0.85rem; }}
  .node-result.ok {{ color: #2ecc71; }}
  .node-result.err {{ color: #e74c3c; }}
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 0.5rem;
  }}
  .badge.de  {{ background: #1abc9c33; color: #1abc9c; }}
  .badge.di  {{ background: #2ecc7133; color: #2ecc71; }}
  .badge.an  {{ background: #3498db33; color: #3498db; }}
  .badge.rt  {{ background: #9b59b633; color: #9b59b6; }}
  .badge.go  {{ background: #e74c3c33; color: #e74c3c; }}
  .badge.ai  {{ background: #f1c40f33; color: #f1c40f; }}
  .summary {{
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-top: 2rem;
  }}
  .summary h2 {{ color: #58a6ff; margin-bottom: 1rem; font-size: 1.2rem; }}
  .summary-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 1rem;
  }}
  .stat-box {{
    text-align: center;
    padding: 1rem;
    border-radius: 8px;
    background: #0d1117;
    border: 1px solid #30363d;
  }}
  .stat-box .number {{
    font-size: 2rem;
    font-weight: 700;
  }}
  .stat-box .label {{
    color: #8b949e;
    font-size: 0.8rem;
    margin-top: 0.3rem;
  }}
  .stat-box.total .number {{ color: #58a6ff; }}
  .stat-box.passed .number {{ color: #2ecc71; }}
  .stat-box.failed .number {{ color: #e74c3c; }}
  .stat-box.agents .number {{ color: #f0883e; }}
  .footer {{
    text-align: center;
    color: #484f58;
    font-size: 0.8rem;
    margin-top: 2rem;
  }}
</style>
</head>
<body>

<div class="header">
  <h1>🧠 Fabric-MAS Agent Workflow</h1>
  <div class="prompt">"{html.escape(plan.prompt)}"</div>
</div>

<div class="flow-container">
  <div class="flow-line"></div>

  <!-- Orchestrator node -->
  <div class="node" style="animation-delay: 0s;">
    <div class="node-dot orchestrator"></div>
    <div class="node-card orch">
      <div class="node-title">
        🧠 <span class="agent">Orchestrator</span> receives prompt
      </div>
      <div class="node-desc">LLM Planner decomposes into {len(plan.steps)} step(s)</div>
    </div>
  </div>

{steps_html}
</div>

{summary_html}

<div class="footer">
  Generated by Fabric-MAS Workflow Visualizer · {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
</div>

</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("Workflow HTML exported: %s", output_path)
        return output_path

    def _build_steps_html(
        self,
        plan: "ExecutionPlan",
        results: Optional[List["AgentResult"]] = None,
    ) -> str:
        parts = []
        for i, step in enumerate(plan.steps):
            status = "pending"
            result_msg = ""
            if results and i < len(results):
                r = results[i]
                status = "success" if r.success else "failed"
                result_msg = html.escape(r.message[:80]) if r.message else ""

            cat = _agent_category(step.agent_key)
            cat_badge_class = {
                "data_engineering": "de", "data_integration": "di",
                "analytics": "an", "realtime": "rt",
                "governance": "go", "ai_advanced": "ai", "orchestrator": "ai",
            }.get(cat, "ai")
            cat_label = cat.replace("_", " ").title()

            delay = 0.1 + (i + 1) * 0.2
            result_line = ""
            if result_msg:
                res_class = "ok" if status == "success" else "err"
                result_line = f'<div class="node-result {res_class}">{STATUS_ICONS[status][0]} {result_msg}</div>'

            parts.append(f"""
  <div class="node" style="animation-delay: {delay}s;">
    <div class="node-dot {status}"></div>
    <div class="node-card {status}">
      <div class="node-title">
        <span class="step-num">Step {step.step_number}</span> →
        <span class="agent">{html.escape(step.agent_key)}</span>.<span class="op">{html.escape(step.operation)}</span>
        <span class="badge {cat_badge_class}">{cat_label}</span>
      </div>
      <div class="node-desc">{html.escape(step.description or '')}</div>
      {result_line}
    </div>
  </div>""")
        return "\n".join(parts)

    def _build_summary_html(
        self,
        plan: "ExecutionPlan",
        results: Optional[List["AgentResult"]] = None,
    ) -> str:
        if not results:
            return ""

        total = len(results)
        passed = sum(1 for r in results if r.success)
        failed = total - passed
        unique_agents = len(set(s.agent_key for s in plan.steps))

        return f"""
<div class="summary">
  <h2>📊 Execution Summary</h2>
  <div class="summary-grid">
    <div class="stat-box total">
      <div class="number">{total}</div>
      <div class="label">Total Steps</div>
    </div>
    <div class="stat-box passed">
      <div class="number">{passed}</div>
      <div class="label">Passed</div>
    </div>
    <div class="stat-box failed">
      <div class="number">{failed}</div>
      <div class="label">Failed</div>
    </div>
    <div class="stat-box agents">
      <div class="number">{unique_agents}</div>
      <div class="label">Agents Used</div>
    </div>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Convenience: integrate with orchestrator
# ---------------------------------------------------------------------------
def visualize_execution(
    plan: "ExecutionPlan",
    results: Optional[List["AgentResult"]] = None,
    export_html: bool = True,
) -> Optional[str]:
    """
    One-call helper: render to terminal + optionally export HTML.
    Returns the HTML file path if exported.
    """
    viz = WorkflowVisualizer()
    viz.render_plan(plan, results)
    if export_html:
        return viz.export_html(plan, results)
    return None
