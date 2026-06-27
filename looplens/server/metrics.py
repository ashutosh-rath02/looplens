"""Run-level metrics and loop-health scoring (PRD section 18).

Computed on demand from the stored events and warnings of a run.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from datetime import datetime

from . import db
from .models import MetricsOut

# Health penalty per warning type (PRD section 18). Keys are the canonical
# warning `type` strings produced by the detectors (Phase 6).
WARNING_PENALTIES: dict[str, int] = {
    "repeated_tool_call": 15,
    "repeated_tool_call_similar_input": 20,
    "retry_storm": 20,
    "no_progress": 30,
    "long_running_step": 10,
    "cost_spike": 15,
}
FAILED_RUN_PENALTY = 30


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _duration_sec(run: sqlite3.Row, events: list[sqlite3.Row]) -> float:
    start = _parse_ts(run["started_at"])
    end = _parse_ts(run["ended_at"])
    if start is None and events:
        start = _parse_ts(events[0]["timestamp"])
    if end is None and events:
        end = _parse_ts(events[-1]["timestamp"])
    if start and end:
        return max(0.0, (end - start).total_seconds())
    return 0.0


def _health(score: int, run_status: str | None) -> str:
    if run_status == "failed":
        return "Failed"
    if score >= 80:
        return "Healthy"
    if score >= 50:
        return "Warning"
    return "Likely stuck"


def compute_metrics(conn: sqlite3.Connection, run: sqlite3.Row) -> MetricsOut:
    run_id = run["id"]
    events = db.list_events(conn, run_id)
    warnings = db.list_warnings(conn, run_id)

    latencies = [e["latency_ms"] for e in events if e["latency_ms"] is not None]
    tools = Counter(
        e["tool"] or e["name"]
        for e in events
        if e["type"] == "tool_call_started" and (e["tool"] or e["name"])
    )
    agents = Counter(e["agent"] for e in events if e["agent"])

    score = 100
    for w in warnings:
        score -= WARNING_PENALTIES.get(w["type"], 0)
    if run["status"] == "failed":
        score -= FAILED_RUN_PENALTY
    score = max(0, min(100, score))

    return MetricsOut(
        run_id=run_id,
        total_events=len(events),
        total_duration_sec=round(_duration_sec(run, events), 3),
        total_llm_calls=sum(1 for e in events if e["type"] == "llm_call_started"),
        total_tool_calls=sum(1 for e in events if e["type"] == "tool_call_started"),
        total_retries=sum(1 for e in events if e["type"] == "retry_triggered"),
        total_handoffs=sum(1 for e in events if e["type"] == "handoff_started"),
        total_errors=sum(1 for e in events if (e["type"] or "").endswith("_failed")),
        total_tokens=sum(e["tokens"] or 0 for e in events),
        estimated_cost=round(sum(e["cost"] or 0 for e in events), 6),
        average_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else 0,
        max_latency_ms=max(latencies) if latencies else 0,
        most_used_tool=tools.most_common(1)[0][0] if tools else None,
        most_active_agent=agents.most_common(1)[0][0] if agents else None,
        warnings_count=len(warnings),
        health_score=score,
        loop_health_status=_health(score, run["status"]),
    )
