"""LoopLens API routes (PRD section 14.3)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .. import __version__
from . import db
from .ingest import store_event
from .metrics import compute_metrics
from .models import EventIn, EventOut, MetricsOut, RunCreate, RunOut, RunSummary, WarningOut
from .websocket import sse_run_stream

router = APIRouter(prefix="/api")


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


@router.get("/runs/{run_id}/stream")
async def stream_run(run_id: str, request: Request) -> StreamingResponse:
    """Server-Sent Events: live events, metrics, and warnings for a run."""
    return StreamingResponse(
        sse_run_stream(run_id, request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --- events ----------------------------------------------------------------

@router.post("/events", response_model=EventOut, status_code=201)
def ingest_event(body: EventIn) -> EventOut:
    with db.connect() as conn:
        stored, _ = store_event(
            conn,
            run_id=body.run_id,
            type=body.type,
            event_id=body.event_id,
            timestamp=body.timestamp,
            sequence=body.sequence,
            agent=body.agent,
            name=body.name,
            status=body.status,
            model=body.model,
            tool=body.tool,
            input=body.input,
            output=body.output,
            error=body.error,
            tokens=body.tokens,
            cost=body.cost,
            latency_ms=body.latency_ms,
            parent_event_id=body.parent_event_id,
            span_id=body.span_id,
            trace_id=body.trace_id,
            metadata=body.metadata,
        )
    return EventOut.from_row(stored)
