"""Tests for the MCP server (read-only loop-health tools).

Populates a temp SQLite db through the real ingestion pipeline (so the
detectors actually fire), then exercises the MCP layer two ways: the pure
diagnosis helpers directly, and the registered FastMCP tools end to end.
"""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def populated(tmp_path, monkeypatch):
    """A db with one healthy run and one looping run; yields the db path."""
    monkeypatch.setenv("LOOPLENS_DB_PATH", str(tmp_path / "t.db"))
    from looplens.server.app import app

    with TestClient(app) as c:
        # A clean run.
        c.post("/api/runs", json={"id": "ok", "name": "healthy"})
        c.post("/api/events", json={"run_id": "ok", "type": "run_started"})
        c.post("/api/events", json={"run_id": "ok", "type": "tool_call_started",
                                    "tool": "lookup", "input": {"q": "a"}})
        c.post("/api/events", json={"run_id": "ok", "type": "tool_call_completed",
                                    "tool": "lookup"})

        # A run that loops on the same tool with the same input -> warnings.
        c.post("/api/runs", json={"id": "loop", "name": "stuck"})
        c.post("/api/events", json={"run_id": "loop", "type": "run_started"})
        for _ in range(4):
            c.post("/api/events", json={"run_id": "loop", "type": "tool_call_started",
                                        "tool": "web_search", "input": {"q": "same"}})
            c.post("/api/events", json={"run_id": "loop", "type": "tool_call_completed",
                                        "tool": "web_search"})
    return tmp_path / "t.db"


def test_diagnosis_payload_reports_the_loop(populated):
    from looplens.mcp import server as mcp_server
    from looplens.server import db

    with db.connect() as conn:
        payload = mcp_server._diagnosis_payload(conn, db.get_run(conn, "loop"))

    assert payload["run_id"] == "loop"
    assert payload["health_score"] < 100
    assert payload["loop_health_status"] in ("Warning", "Likely stuck")
    assert payload["warning_count"] >= 1
    assert "web_search" in payload["verdict"]
    # Every warning points at a culprit event so the agent can jump to the fix.
    assert all("event_id" in w for w in payload["warnings"])


def test_diagnosis_payload_clean_run_is_healthy(populated):
    from looplens.mcp import server as mcp_server
    from looplens.server import db

    with db.connect() as conn:
        payload = mcp_server._diagnosis_payload(conn, db.get_run(conn, "ok"))

    assert payload["health_score"] == 100
    assert payload["loop_health_status"] == "Healthy"
    assert payload["warning_count"] == 0
    assert "No loops detected" in payload["verdict"]


def test_run_summary_carries_health(populated):
    from looplens.mcp import server as mcp_server
    from looplens.server import db

    with db.connect() as conn:
        summary = mcp_server._run_summary(conn, db.get_run(conn, "loop"))

    assert summary["event_count"] > 0
    assert summary["warning_count"] >= 1
    assert summary["health_score"] < 100


# --- end-to-end through the registered FastMCP tools ------------------------

def _call(server, name, **arguments):
    """Invoke a FastMCP tool by name and return its parsed result.

    Normalises across mcp versions: newer returns
    ``(content_blocks, structured_content)``; older returns a list of content
    blocks whose text is the JSON-encoded return value.
    """
    result = asyncio.run(server.call_tool(name, arguments))
    if isinstance(result, tuple):
        structured = result[1]
        if isinstance(structured, dict) and set(structured) == {"result"}:
            return structured["result"]
        return structured
    return json.loads(result[0].text)


def test_build_mcp_registers_the_tools(populated):
    from looplens.mcp import build_mcp

    server = build_mcp()
    names = {t.name for t in asyncio.run(server.list_tools())}
    assert {
        "list_runs",
        "latest_run_diagnosis",
        "get_run_diagnosis",
        "get_run_warnings",
        "get_run_metrics",
        "get_run_events",
    } <= names


def test_tool_latest_run_diagnosis(populated):
    from looplens.mcp import build_mcp

    server = build_mcp()
    out = _call(server, "latest_run_diagnosis")
    # Most recent run is the looping one.
    assert out["run_id"] == "loop"
    assert "web_search" in out["verdict"]


def test_tool_get_run_diagnosis_unknown_run_errors(populated):
    from looplens.mcp import build_mcp

    server = build_mcp()
    with pytest.raises(Exception):
        _call(server, "get_run_diagnosis", run_id="nope")
