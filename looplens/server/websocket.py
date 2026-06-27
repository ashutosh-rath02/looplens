"""Real-time event streaming to the UI (PRD section 14.3 / Phase 5).

Transport: **Server-Sent Events**. For a one-directional server→UI stream this is
simpler and more robust than WebSocket (auto-reconnect, plain HTTP, no upgrade).

Mechanism: poll. The generator re-reads the run from SQLite every POLL seconds
and pushes any events past the last sequence it sent, along with fresh metrics
and warnings. Polling avoids bridging the sync DB/ingestion path to async pub/sub
and is plenty responsive for a local single-user debugger. DB reads run in a
threadpool so the event loop is never blocked.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import Request
from fastapi.concurrency import run_in_threadpool

from . import db
from .metrics import compute_metrics
from .models import EventOut, WarningOut

POLL_SECONDS = 0.5


def _collect(run_id: str, last_seq: int):
    """Synchronous DB snapshot since ``last_seq`` (runs in a threadpool)."""
    with db.connect() as conn:
        run = db.get_run(conn, run_id)
        if run is None:
            return None
        events = db.list_events(conn, run_id)
        new = [EventOut.from_row(e).model_dump() for e in events if e["sequence"] > last_seq]
        max_seq = max((e["sequence"] for e in events), default=last_seq)
        metrics = compute_metrics(conn, run).model_dump()
        warnings = [WarningOut.from_row(w).model_dump() for w in db.list_warnings(conn, run_id)]
        return new, max_seq, metrics, warnings, run["status"]


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, default=str)}\n\n"


async def sse_run_stream(run_id: str, request: Request) -> AsyncIterator[str]:
    last_seq = 0
    last_warn_count = -1
    while True:
        if await request.is_disconnected():
            return

        snapshot = await run_in_threadpool(_collect, run_id, last_seq)
        if snapshot is None:
            # Run not created yet — keep the connection open and retry.
            yield ": waiting\n\n"
        else:
            new, last_seq, metrics, warnings, status = snapshot
            if new or len(warnings) != last_warn_count:
                last_warn_count = len(warnings)
                yield _sse({
                    "type": "update",
                    "events": new,
                    "metrics": metrics,
                    "warnings": warnings,
                    "status": status,
                })
            else:
                yield ": keepalive\n\n"

        await asyncio.sleep(POLL_SECONDS)
