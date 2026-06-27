"""Pydantic models for the LoopLens API (PRD sections 15, 16, 18).

These describe the wire format. Storage rows are plain SQLite columns; the
``from_row`` helpers convert a row back into an API model.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from pydantic import BaseModel, Field


def _loads(value: str | None) -> Any:
    return None if value in (None, "") else json.loads(value)


# --- runs ------------------------------------------------------------------

class RunCreate(BaseModel):
    id: str | None = None
    name: str | None = None
    project: str = "default"
    metadata: dict | None = None


class RunOut(BaseModel):
    id: str
    name: str | None = None
    project: str | None = None
    status: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    total_cost: float = 0
    total_tokens: int = 0
    metadata: dict | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "RunOut":
        return cls(
            id=row["id"],
            name=row["name"],
            project=row["project"],
            status=row["status"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            total_cost=row["total_cost"] or 0,
            total_tokens=row["total_tokens"] or 0,
            metadata=_loads(row["metadata_json"]),
        )


class RunSummary(RunOut):
    """Run plus cheap counts for the runs-list screen."""

    event_count: int = 0
    warning_count: int = 0


# --- events ----------------------------------------------------------------

class EventIn(BaseModel):
    event_id: str | None = None
    run_id: str
    timestamp: str | None = None
    sequence: int | None = None
    type: str
    agent: str | None = None
    name: str | None = None
    status: str | None = None
    model: str | None = None
    tool: str | None = None
    input: Any | None = None
    output: Any | None = None
    error: Any | None = None
    tokens: int | None = None
    cost: float | None = None
    latency_ms: int | None = None
    parent_event_id: str | None = None
    span_id: str | None = None
    trace_id: str | None = None
    metadata: dict | None = None


class EventOut(BaseModel):
    event_id: str
    run_id: str
    sequence: int
    timestamp: str
    type: str
    agent: str | None = None
    name: str | None = None
    status: str | None = None
    model: str | None = None
    tool: str | None = None
    input: Any | None = None
    output: Any | None = None
    error: Any | None = None
    tokens: int | None = None
    cost: float | None = None
    latency_ms: int | None = None
    parent_event_id: str | None = None
    span_id: str | None = None
    trace_id: str | None = None
    metadata: dict | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "EventOut":
        return cls(
            event_id=row["id"],
            run_id=row["run_id"],
            sequence=row["sequence"],
            timestamp=row["timestamp"],
            type=row["type"],
            agent=row["agent"],
            name=row["name"],
            status=row["status"],
            model=row["model"],
            tool=row["tool"],
            input=_loads(row["input_json"]),
            output=_loads(row["output_json"]),
            error=_loads(row["error_json"]),
            tokens=row["tokens"],
            cost=row["cost"],
            latency_ms=row["latency_ms"],
            parent_event_id=row["parent_event_id"],
            span_id=row["span_id"],
            trace_id=row["trace_id"],
            metadata=_loads(row["metadata_json"]),
        )


# --- warnings --------------------------------------------------------------

class WarningOut(BaseModel):
    warning_id: str
    run_id: str
    event_id: str | None = None
    type: str
    severity: str
    message: str
    details: dict | None = None
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "WarningOut":
        return cls(
            warning_id=row["id"],
            run_id=row["run_id"],
            event_id=row["event_id"],
            type=row["type"],
            severity=row["severity"],
            message=row["message"],
            details=_loads(row["details_json"]),
            created_at=row["created_at"],
        )


# --- metrics ---------------------------------------------------------------

class MetricsOut(BaseModel):
    run_id: str
    total_events: int = 0
    total_duration_sec: float = 0
    total_llm_calls: int = 0
    total_tool_calls: int = 0
    total_retries: int = 0
    total_handoffs: int = 0
    total_errors: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0
    average_latency_ms: float = 0
    max_latency_ms: int = 0
    most_used_tool: str | None = None
    most_active_agent: str | None = None
    warnings_count: int = 0
    health_score: int = 100
    loop_health_status: str = "Healthy"
