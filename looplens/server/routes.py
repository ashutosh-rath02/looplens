"""LoopLens API routes (PRD section 14.3)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import __version__
from . import db
from .detectors import run_detectors
from .metrics import compute_metrics
from .models import EventIn, EventOut, MetricsOut, RunCreate, RunOut, RunSummary, WarningOut

router = APIRouter(prefix="/api")

# Event types that move a run out of the "running" state.
_TERMINAL_STATUS = {
    "run_completed": "completed",
    "run_failed": "failed",
}


@router.get("/health")
def health() -> dict:
    return {"status": "healthy", "service": "looplens", "version": __version__}


# --- runs ------------------------------------------------------------------

@router.post("/runs", response_model=RunOut, status_code=201)
def create_run(body: RunCreate) -> RunOut:
    with db.connect() as conn:
        row = db.create_run(
            conn,
            id=body.id,
            name=body.name,
            project=body.project,
            metadata=body.metadata,
        )
    return RunOut.from_row(row)


@router.get("/runs", response_model=list[RunSummary])
def list_runs() -> list[RunSummary]:
    with db.connect() as conn:
        rows = db.list_runs(conn)
        out: list[RunSummary] = []
        for row in rows:
            summary = RunSummary.from_row(row)
            summary.event_count = db.count_events(conn, row["id"])
            summary.warning_count = db.count_warnings(conn, row["id"])
            out.append(summary)
    return out


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(run_id: str) -> RunOut:
    with db.connect() as conn:
        row = db.get_run(conn, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="run not found")
    return RunOut.from_row(row)


@router.get("/runs/{run_id}/events", response_model=list[EventOut])
def get_run_events(run_id: str) -> list[EventOut]:
    with db.connect() as conn:
        if db.get_run(conn, run_id) is None:
            raise HTTPException(status_code=404, detail="run not found")
        rows = db.list_events(conn, run_id)
    return [EventOut.from_row(r) for r in rows]


@router.get("/runs/{run_id}/warnings", response_model=list[WarningOut])
def get_run_warnings(run_id: str) -> list[WarningOut]:
    with db.connect() as conn:
        if db.get_run(conn, run_id) is None:
            raise HTTPException(status_code=404, detail="run not found")
        rows = db.list_warnings(conn, run_id)
    return [WarningOut.from_row(r) for r in rows]


@router.get("/runs/{run_id}/metrics", response_model=MetricsOut)
def get_run_metrics(run_id: str) -> MetricsOut:
    with db.connect() as conn:
        row = db.get_run(conn, run_id)
        if row is None:
            raise HTTPException(status_code=404, detail="run not found")
        return compute_metrics(conn, row)


# --- events ----------------------------------------------------------------

@router.post("/events", response_model=EventOut, status_code=201)
def ingest_event(body: EventIn) -> EventOut:
    with db.connect() as conn:
        # The SDK creates the run first, but stay forgiving for imports/JSONL.
        if db.get_run(conn, body.run_id) is None:
            db.create_run(conn, id=body.run_id, name=body.run_id, project="default")

        event_id = body.event_id or db.gen_id("evt")
        timestamp = body.timestamp or db.now_iso()
        sequence = body.sequence if body.sequence is not None else db.next_sequence(conn, body.run_id)

        row = {
            "id": event_id,
            "run_id": body.run_id,
            "sequence": sequence,
            "timestamp": timestamp,
            "type": body.type,
            "agent": body.agent,
            "name": body.name,
            "status": body.status,
            "model": body.model,
            "tool": body.tool,
            "input_json": db.dumps(body.input),
            "output_json": db.dumps(body.output),
            "error_json": db.dumps(body.error),
            "tokens": body.tokens,
            "cost": body.cost,
            "latency_ms": body.latency_ms,
            "parent_event_id": body.parent_event_id,
            "span_id": body.span_id,
            "trace_id": body.trace_id,
            "metadata_json": db.dumps(body.metadata),
        }
        db.insert_event(conn, row)
        db.add_run_totals(conn, body.run_id, body.cost or 0, body.tokens or 0)

        # Run lifecycle.
        if body.type in _TERMINAL_STATUS:
            db.set_run_status(conn, body.run_id, _TERMINAL_STATUS[body.type], timestamp)

        # Loop detection (Phase 6: no-op stub today).
        for warning in run_detectors(conn, body.run_id):
            db.insert_warning(conn, warning)

        stored = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()

    return EventOut.from_row(stored)
