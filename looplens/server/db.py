"""SQLite storage for LoopLens (PRD section 19).

Three tables: runs, events, warnings. Connections are opened per operation
(SQLite handles this fine at local-dev volume) with WAL enabled so the API and
the future WebSocket writer don't block each other.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from ..config import get_config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  name TEXT,
  project TEXT,
  status TEXT,
  started_at TEXT,
  ended_at TEXT,
  total_cost REAL DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  run_id TEXT,
  sequence INTEGER,
  timestamp TEXT,
  type TEXT,
  agent TEXT,
  name TEXT,
  status TEXT,
  model TEXT,
  tool TEXT,
  input_json TEXT,
  output_json TEXT,
  error_json TEXT,
  tokens INTEGER,
  cost REAL,
  latency_ms INTEGER,
  parent_event_id TEXT,
  span_id TEXT,
  trace_id TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS warnings (
  id TEXT PRIMARY KEY,
  run_id TEXT,
  event_id TEXT,
  type TEXT,
  severity TEXT,
  message TEXT,
  details_json TEXT,
  created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id, sequence);
CREATE INDEX IF NOT EXISTS idx_warnings_run ON warnings(run_id);
"""


# --- helpers ---------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def dumps(value: Any) -> str | None:
    return None if value is None else json.dumps(value, default=str)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(get_config().db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(_SCHEMA)


# --- runs ------------------------------------------------------------------

def create_run(
    conn: sqlite3.Connection,
    *,
    id: str | None = None,
    name: str | None = None,
    project: str = "default",
    status: str = "running",
    started_at: str | None = None,
    metadata: dict | None = None,
) -> sqlite3.Row:
    rid = id or gen_id("run")
    conn.execute(
        """INSERT OR IGNORE INTO runs
           (id, name, project, status, started_at, metadata_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (rid, name or rid, project, status, started_at or now_iso(), dumps(metadata or {})),
    )
    return get_run(conn, rid)


def get_run(conn: sqlite3.Connection, run_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()


def list_runs(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM runs ORDER BY started_at DESC").fetchall()


def set_run_status(conn: sqlite3.Connection, run_id: str, status: str, ended_at: str | None) -> None:
    conn.execute(
        "UPDATE runs SET status = ?, ended_at = ? WHERE id = ?",
        (status, ended_at, run_id),
    )


def add_run_totals(conn: sqlite3.Connection, run_id: str, cost: float, tokens: int) -> None:
    conn.execute(
        """UPDATE runs
           SET total_cost = COALESCE(total_cost, 0) + ?,
               total_tokens = COALESCE(total_tokens, 0) + ?
           WHERE id = ?""",
        (cost or 0, tokens or 0, run_id),
    )


# --- events ----------------------------------------------------------------

def next_sequence(conn: sqlite3.Connection, run_id: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(sequence), 0) AS seq FROM events WHERE run_id = ?", (run_id,)
    ).fetchone()
    return int(row["seq"]) + 1


def insert_event(conn: sqlite3.Connection, row: dict) -> bool:
    """Insert an event. Idempotent on event id; returns True if a new row was
    written (False if it already existed), so callers don't double-count."""
    cur = conn.execute(
        """INSERT OR IGNORE INTO events
           (id, run_id, sequence, timestamp, type, agent, name, status, model, tool,
            input_json, output_json, error_json, tokens, cost, latency_ms,
            parent_event_id, span_id, trace_id, metadata_json)
           VALUES (:id, :run_id, :sequence, :timestamp, :type, :agent, :name, :status,
                   :model, :tool, :input_json, :output_json, :error_json, :tokens, :cost,
                   :latency_ms, :parent_event_id, :span_id, :trace_id, :metadata_json)""",
        row,
    )
    return cur.rowcount > 0


def list_events(conn: sqlite3.Connection, run_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM events WHERE run_id = ? ORDER BY sequence ASC", (run_id,)
    ).fetchall()


def count_events(conn: sqlite3.Connection, run_id: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) AS c FROM events WHERE run_id = ?", (run_id,)
    ).fetchone()["c"]


# --- warnings --------------------------------------------------------------

def insert_warning(conn: sqlite3.Connection, row: dict) -> None:
    conn.execute(
        """INSERT INTO warnings
           (id, run_id, event_id, type, severity, message, details_json, created_at)
           VALUES (:id, :run_id, :event_id, :type, :severity, :message, :details_json,
                   :created_at)""",
        row,
    )


def list_warnings(conn: sqlite3.Connection, run_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM warnings WHERE run_id = ? ORDER BY created_at ASC", (run_id,)
    ).fetchall()


def count_warnings(conn: sqlite3.Connection, run_id: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) AS c FROM warnings WHERE run_id = ?", (run_id,)
    ).fetchone()["c"]
