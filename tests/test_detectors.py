"""Tests for the loop detectors (Phase 6), driven through the real ingestion
pipeline with FastAPI's in-process TestClient against a temp SQLite db.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LOOPLENS_DB_PATH", str(tmp_path / "t.db"))
    from looplens.server.app import app

    with TestClient(app) as c:
        yield c


def ev(client, run_id, type, **kw):
    r = client.post("/api/events", json={"run_id": run_id, "type": type, **kw})
    assert r.status_code == 201, r.text


def warning_types(client, run_id):
    return {w["type"] for w in client.get(f"/api/runs/{run_id}/warnings").json()}


def test_repeated_similar_and_no_progress(client):
    client.post("/api/runs", json={"id": "r1", "name": "loop"})
    ev(client, "r1", "run_started")
    for _ in range(4):
        ev(client, "r1", "tool_call_started", tool="web_search", input={"q": "same"})
        ev(client, "r1", "tool_call_completed", tool="web_search")

    warnings = client.get("/api/runs/r1/warnings").json()
    types = {w["type"] for w in warnings}
    assert "repeated_tool_call" in types
    assert "repeated_tool_call_similar_input" in types
    assert "no_progress" in types
    # Deduped: a single repeated_tool_call for web_search, not one per event.
    assert sum(1 for w in warnings if w["type"] == "repeated_tool_call") == 1


def test_repeated_tool_detected_in_interleaved_react_trace(client):
    # A ReAct step interleaves llm_call_* and tool_call_* events. The window must
    # slide over tool calls, not raw events, or these searches never trip the rule.
    # Queries are deliberately dissimilar so similar_input does NOT mask the result.
    client.post("/api/runs", json={"id": "rt", "name": "react"})
    queries = ["how to deploy", "retry backoff config", "auth token rotation", "stream the logs"]
    for q in queries:
        ev(client, "rt", "llm_call_started", model="m")
        ev(client, "rt", "llm_call_completed", model="m")
        ev(client, "rt", "tool_call_started", tool="search", input={"q": q})
        ev(client, "rt", "tool_call_completed", tool="search")

    types = warning_types(client, "rt")
    assert "repeated_tool_call" in types  # caught despite interleaved llm events
    assert "repeated_tool_call_similar_input" not in types  # inputs differ -> not similar


def test_exact_repeat_detected_for_identical_input(client):
    # Byte-identical args three times is the high-confidence exact-repeat signal.
    client.post("/api/runs", json={"id": "ex", "name": "exact"})
    for _ in range(3):
        ev(client, "ex", "tool_call_started", tool="fetch", input={"url": "https://a.com"})
        ev(client, "ex", "tool_call_completed", tool="fetch")
    assert "repeated_tool_call_exact_input" in warning_types(client, "ex")


def test_no_exact_repeat_for_distinct_inputs(client):
    # Same tool, but every call has different args -> no byte-identical group.
    client.post("/api/runs", json={"id": "ed", "name": "distinct"})
    for u in ["https://a.com", "https://b.com", "https://c.com"]:
        ev(client, "ed", "tool_call_started", tool="fetch", input={"url": u})
        ev(client, "ed", "tool_call_completed", tool="fetch")
    assert "repeated_tool_call_exact_input" not in warning_types(client, "ed")


def test_handoff_bounce(client):
    client.post("/api/runs", json={"id": "hb", "name": "bounce"})
    for a in ["researcher", "planner", "researcher", "planner"]:
        ev(client, "hb", "handoff_started", agent=a)
    assert "handoff_bounce" in warning_types(client, "hb")


def test_no_handoff_bounce_for_linear_flow(client):
    client.post("/api/runs", json={"id": "hl", "name": "linear"})
    for a in ["planner", "researcher", "writer"]:  # 3 distinct agents, no ping-pong
        ev(client, "hl", "handoff_started", agent=a)
    assert "handoff_bounce" not in warning_types(client, "hl")


def test_no_progress_clears_when_state_updates(client):
    client.post("/api/runs", json={"id": "rp", "name": "progress"})
    for _ in range(4):
        ev(client, "rp", "tool_call_started", tool="check", input={"q": "x"})
        ev(client, "rp", "state_updated", name="check")  # progress between calls
    assert "no_progress" not in warning_types(client, "rp")


def test_retry_storm(client):
    client.post("/api/runs", json={"id": "r2", "name": "retry"})
    for _ in range(3):
        ev(client, "r2", "retry_triggered", tool="charge")
    assert "retry_storm" in warning_types(client, "r2")


def test_long_running_step(client):
    client.post("/api/runs", json={"id": "r3", "name": "slow"})
    ev(client, "r3", "tool_call_completed", tool="ocr", latency_ms=40000)
    assert "long_running_step" in warning_types(client, "r3")


def test_cost_spike(client):
    client.post("/api/runs", json={"id": "r4", "name": "cost"})
    ev(client, "r4", "llm_call_completed", cost=0.01)
    ev(client, "r4", "llm_call_completed", cost=0.01)
    ev(client, "r4", "llm_call_completed", cost=0.20)
    assert "cost_spike" in warning_types(client, "r4")


def test_healthy_run_has_no_warnings(client):
    client.post("/api/runs", json={"id": "r5", "name": "ok"})
    ev(client, "r5", "run_started")
    ev(client, "r5", "tool_call_started", tool="a", input={"x": 1})
    ev(client, "r5", "tool_call_completed", tool="a")
    ev(client, "r5", "run_completed", status="completed")

    assert client.get("/api/runs/r5/warnings").json() == []
    assert client.get("/api/runs/r5/metrics").json()["loop_health_status"] == "Healthy"
