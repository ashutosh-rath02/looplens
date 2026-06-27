"""Shared event-ingestion path.

Both the SDK-facing ``POST /api/events`` route and the OpenTelemetry receiver
(``POST /v1/traces``) funnel through ``store_event`` so loop detection, run
totals, lifecycle, and the live stream behave identically no matter how an event
arrived.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from . import db
from .detectors import run_detectors

# Event types that move a run out of the "running" state.
_TERMINAL_STATUS = {
    "run_completed": "completed",
    "run_failed": "failed",
}


def store_event(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    type: str,  # noqa: A002
    event_id: str | None = None,
    timestamp: str | None = None,
    sequence: int | None = None,
    agent: str | None = None,
    name: str | None = None,
    status: str | None = None,
    model: str | None = None,
    tool: str | None = None,
    input: Any = None,  # noqa: A002
    output: Any = None,
    error: Any = None,
    tokens: int | None = None,
    cost: float | None = None,
    latency_ms: int | None = None,
    parent_event_id: str | None = None,
    span_id: str | None = None,
    trace_id: str | None = None,
    metadata: Any = None,
    detect: bool = True,
) -> tuple[sqlite3.Row, bool]:
    """Insert one event and apply its side effects. Returns (stored_row, inserted).

    ``detect=False`` skips loop detection so a bulk import (e.g. a whole OTel
    trace) can insert all events first and run the detectors once at the end.
    """
    # The SDK creates the run first, but stay forgiving for imports / OTel.
    if db.get_run(conn, run_id) is None:
        db.create_run(conn, id=run_id, name=run_id, project="default")

    event_id = event_id or db.gen_id("evt")
    timestamp = timestamp or db.now_iso()
    sequence = sequence if sequence is not None else db.next_sequence(conn, run_id)

    row = {
        "id": event_id,
        "run_id": run_id,
        "sequence": sequence,
        "timestamp": timestamp,
        "type": type,
        "agent": agent,
        "name": name,
        "status": status,
        "model": model,
        "tool": tool,
        "input_json": db.dumps(input),
        "output_json": db.dumps(output),
        "error_json": db.dumps(error),
        "tokens": tokens,
        "cost": cost,
        "latency_ms": latency_ms,
        "parent_event_id": parent_event_id,
        "span_id": span_id,
        "trace_id": trace_id,
        "metadata_json": db.dumps(metadata),
    }
    inserted = db.insert_event(conn, row)
    if inserted:
        db.add_run_totals(conn, run_id, cost or 0, tokens or 0)
        if type in _TERMINAL_STATUS:
            db.set_run_status(conn, run_id, _TERMINAL_STATUS[type], timestamp)
        if detect:
            run_detectors(conn, run_id)

    stored = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    return stored, inserted
