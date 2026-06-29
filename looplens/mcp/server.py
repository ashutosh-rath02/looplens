"""The LoopLens MCP server: read-only loop-health tools over the local store.

The server reads the same SQLite database the dashboard uses (via
``looplens.server.db``) and reuses the existing health scoring
(``score_health``) and metrics (``compute_metrics``), so an MCP client sees
exactly the same verdicts as the UI — no second source of truth.

Tools (all read-only):
  list_runs               recent runs with loop health at a glance
  latest_run_diagnosis    the verdict for the most recent run ("did it loop?")
  get_run_diagnosis       verdict + warnings (with culprit event ids) for a run
  get_run_warnings        the raw loop warnings for a run
  get_run_metrics         token/cost/latency/health metrics for a run
  get_run_events          the event timeline for a run (to inspect the loop)
"""

from __future__ import annotations

from typing import Any

from .. import __version__
from ..server import db
from ..server.metrics import compute_metrics, score_health
from ..server.models import EventOut, WarningOut

_MCP_EXTRA_HINT = (
    "The LoopLens MCP server needs extra dependencies.\n\n"
    "    pip install 'looplens[mcp]'\n"
)

_INSTRUCTIONS = (
    "LoopLens is a local-first loop debugger for AI agents. Use these tools to "
    "check whether an agent run got stuck in a loop, burned tokens, or stopped "
    "making progress, and to find the exact event to fix. Start with "
    "latest_run_diagnosis (or list_runs) to get a verdict, then get_run_warnings "
    "/ get_run_events to drill in. Every warning carries the culprit event_id."
)


# --- diagnosis (mirrors ui/src/lib.ts so the verdict reads identically) -----

# Most-diagnostic warning first — used to pick the headline cause.
_WARNING_PRIORITY = (
    "no_progress",
    "empty_result_loop",
    "repeated_tool_call_exact_input",
    "repeated_tool_call_similar_input",
    "repeated_tool_call",
    "handoff_bounce",
    "retry_storm",
    "cost_budget_exceeded",
    "cost_spike",
    "long_running_step",
)

_WARNING_TITLES = {
    "repeated_tool_call": "Repeated tool call",
    "repeated_tool_call_similar_input": "Repeated tool call · similar input",
    "repeated_tool_call_exact_input": "Repeated tool call · exact input",
    "no_progress": "No-progress loop",
    "empty_result_loop": "Empty-result loop",
    "retry_storm": "Retry storm",
    "long_running_step": "Long-running step",
    "cost_spike": "Cost spike",
    "cost_budget_exceeded": "Cost budget exceeded",
    "handoff_bounce": "Handoff bounce",
}


def _rank(warning_type: str) -> int:
    try:
        return _WARNING_PRIORITY.index(warning_type)
    except ValueError:
        return len(_WARNING_PRIORITY)


def _warning_phrase(warning_type: str, d: dict) -> str:
    tool = d.get("tool")
    count = d.get("count")
    if warning_type == "no_progress":
        return f"'{tool}' repeated {count}× with no progress"
    if warning_type == "empty_result_loop":
        return f"'{tool}' returned no results {count}×"
    if warning_type == "repeated_tool_call_exact_input":
        return f"'{tool}' called {count}× with identical input"
    if warning_type == "repeated_tool_call_similar_input":
        return f"'{tool}' called {count}× with near-identical input"
    if warning_type == "repeated_tool_call":
        return f"'{tool}' called {count}× in a loop"
    if warning_type == "handoff_bounce":
        agents = " / ".join(d.get("agents") or [])
        return f"agents {agents} handed off {d.get('count')}× without resolving"
    if warning_type == "retry_storm":
        return f"{d.get('count', 'several')} retries fired without changing strategy"
    if warning_type == "cost_budget_exceeded":
        return "run cost crossed the configured budget"
    if warning_type == "cost_spike":
        return "one step dominated the run's cost"
    if warning_type == "long_running_step":
        return "a step ran far longer than expected"
    return _WARNING_TITLES.get(warning_type, warning_type).lower()


def _diagnose(warnings: list[WarningOut], run_status: str | None) -> str:
    if run_status == "failed":
        return "This run failed."
    if not warnings:
        return "No loops detected — this run looks healthy."
    _, status = score_health(_as_rows(warnings), run_status)
    primary = min(warnings, key=lambda w: _rank(w.type))
    more = len(warnings) - 1
    suffix = f" (+{more} more signal{'s' if more > 1 else ''})" if more > 0 else ""
    return f"{status} — {_warning_phrase(primary.type, primary.details or {})}.{suffix}"


# --- row -> JSON-serialisable dict helpers ----------------------------------

def _as_rows(warnings: list[WarningOut]) -> list[dict]:
    # score_health only reads warning["type"]; give it that from the models.
    return [{"type": w.type} for w in warnings]


def _warning_dict(w: WarningOut) -> dict:
    return {
        "type": w.type,
        "title": _WARNING_TITLES.get(w.type, w.type),
        "severity": w.severity,
        "message": w.message,
        "event_id": w.event_id,  # the culprit event — "where do I fix it?"
        "details": w.details,
    }


def _event_dict(e: EventOut) -> dict:
    return {
        "event_id": e.event_id,
        "sequence": e.sequence,
        "timestamp": e.timestamp,
        "type": e.type,
        "agent": e.agent,
        "name": e.name,
        "tool": e.tool,
        "status": e.status,
        "model": e.model,
        "input": e.input,
        "output": e.output,
        "error": e.error,
        "tokens": e.tokens,
        "cost": e.cost,
        "latency_ms": e.latency_ms,
    }


def _run_summary(conn, row) -> dict:
    warnings = db.list_warnings(conn, row["id"])
    score, status = score_health(warnings, row["status"])
    return {
        "run_id": row["id"],
        "name": row["name"],
        "project": row["project"],
        "status": row["status"],
        "started_at": row["started_at"],
        "ended_at": row["ended_at"],
        "event_count": db.count_events(conn, row["id"]),
        "warning_count": len(warnings),
        "health_score": score,
        "loop_health_status": status,
    }


def _diagnosis_payload(conn, row) -> dict:
    rows = db.list_warnings(conn, row["id"])
    score, status = score_health(rows, row["status"])
    warnings = [WarningOut.from_row(w) for w in rows]
    return {
        "run_id": row["id"],
        "name": row["name"],
        "status": row["status"],
        "health_score": score,
        "loop_health_status": status,
        "verdict": _diagnose(warnings, row["status"]),
        "warning_count": len(warnings),
        "warnings": [_warning_dict(w) for w in warnings],
    }


# --- server -----------------------------------------------------------------

def build_mcp() -> Any:
    """Build the FastMCP server with the LoopLens tools registered.

    The ``mcp`` SDK is imported here (not at module load) so importing
    ``looplens.mcp`` stays cheap and gives a clean install hint if the extra
    is missing.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised via the CLI
        raise ModuleNotFoundError(_MCP_EXTRA_HINT) from exc

    server = FastMCP("looplens", instructions=_INSTRUCTIONS)

    @server.tool()
    def list_runs(limit: int = 20) -> list[dict]:
        """List recent agent runs with their loop health, most recent first.

        Each run includes its health score (0–100), loop-health status
        (Healthy / Warning / Likely stuck / Failed), event count, and warning
        count. Use this to spot which runs got stuck before drilling in.
        """
        with db.connect() as conn:
            rows = db.list_runs(conn)[: max(1, limit)]
            return [_run_summary(conn, r) for r in rows]

    @server.tool()
    def latest_run_diagnosis() -> dict:
        """Diagnose the most recent run: did the agent loop, and where?

        Returns the one-line verdict (e.g. "Likely stuck — 'search' repeated 5×
        with no progress"), the health status, and the loop warnings — each with
        the culprit event_id. The fast answer to "did my last run loop?".
        """
        with db.connect() as conn:
            rows = db.list_runs(conn)
            if not rows:
                raise ValueError("no runs recorded yet")
            return _diagnosis_payload(conn, rows[0])

    @server.tool()
    def get_run_diagnosis(run_id: str) -> dict:
        """Diagnose a specific run by id: verdict, health, and loop warnings.

        Returns the one-line verdict, the health score/status, and every loop
        warning (with its culprit event_id) so you can jump straight to the fix.
        """
        with db.connect() as conn:
            row = db.get_run(conn, run_id)
            if row is None:
                raise ValueError(f"run not found: {run_id}")
            return _diagnosis_payload(conn, row)

    @server.tool()
    def get_run_warnings(run_id: str) -> list[dict]:
        """List the loop warnings raised for a run.

        Each warning has a type, severity, plain-English message, the culprit
        event_id, and the structured details (tool, repeat count, …) behind it.
        """
        with db.connect() as conn:
            if db.get_run(conn, run_id) is None:
                raise ValueError(f"run not found: {run_id}")
            rows = db.list_warnings(conn, run_id)
        return [_warning_dict(WarningOut.from_row(r)) for r in rows]

    @server.tool()
    def get_run_metrics(run_id: str) -> dict:
        """Get token, cost, latency, and loop-health metrics for a run."""
        with db.connect() as conn:
            row = db.get_run(conn, run_id)
            if row is None:
                raise ValueError(f"run not found: {run_id}")
            return compute_metrics(conn, row).model_dump()

    @server.tool()
    def get_run_events(run_id: str, limit: int = 100) -> list[dict]:
        """Get a run's event timeline (LLM calls, tool calls, retries, handoffs).

        Returns the most recent ``limit`` events in order. Use this to inspect
        the loop itself — e.g. the repeated tool call and its input/output.
        """
        with db.connect() as conn:
            if db.get_run(conn, run_id) is None:
                raise ValueError(f"run not found: {run_id}")
            rows = db.list_events(conn, run_id)
        events = [EventOut.from_row(r) for r in rows][-max(1, limit):]
        return [_event_dict(e) for e in events]

    return server


def run_mcp() -> None:
    """Run the LoopLens MCP server over stdio (the default MCP transport)."""
    build_mcp().run()
