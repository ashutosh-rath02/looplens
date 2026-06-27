"""Test the SSE live stream (Phase 5).

We drive the async SSE generator (``sse_run_stream``) directly rather than
consuming it over HTTP via Starlette's ``TestClient``. The stream is infinite by
design (a live dashboard keeps watching), and closing such a stream mid-flight
through ``TestClient`` deadlocks its portal thread on Windows — a limitation of
the test transport, not the server, which streams fine under uvicorn/a browser.

Driving the generator directly is faster, deterministic, cross-platform, and
still exercises the real path: SQLite ingest -> detectors -> metrics -> frame.
Seeding still goes through the real (non-streaming) API so ingestion and loop
detection run exactly as in production.
"""

from __future__ import annotations

import asyncio
import json

from fastapi.testclient import TestClient


class _FakeRequest:
    """Minimal stand-in for starlette.Request used by the generator."""

    async def is_disconnected(self) -> bool:
        return False


async def _first_update(run_id: str) -> dict:
    """Pull frames from the SSE generator until the first ``update`` frame."""
    from looplens.server.websocket import sse_run_stream

    agen = sse_run_stream(run_id, _FakeRequest())
    try:
        for _ in range(50):
            frame = await agen.__anext__()
            if frame.startswith("data:"):
                data = json.loads(frame[len("data:"):])
                if data.get("type") == "update":
                    return data
        raise AssertionError("no update frame received")
    finally:
        await agen.aclose()


def test_sse_streams_snapshot_and_warnings(tmp_path, monkeypatch):
    monkeypatch.setenv("LOOPLENS_DB_PATH", str(tmp_path / "t.db"))
    from looplens.server.app import app

    # Seed through the real (non-streaming) API so ingestion + detectors run.
    with TestClient(app) as c:
        c.post("/api/runs", json={"id": "s1", "name": "s"})
        c.post("/api/events", json={"run_id": "s1", "type": "run_started"})
        for _ in range(3):  # a tiny retry storm so the stream also carries a warning
            c.post("/api/events", json={"run_id": "s1", "type": "retry_triggered", "tool": "x"})

    data = asyncio.run(_first_update("s1"))

    types = {e["type"] for e in data["events"]}
    assert "run_started" in types
    assert any(w["type"] == "retry_storm" for w in data["warnings"])
    assert data["metrics"]["total_events"] >= 4


def test_stream_route_returns_event_stream(tmp_path, monkeypatch):
    """The route wires the SSE generator into a text/event-stream response."""
    monkeypatch.setenv("LOOPLENS_DB_PATH", str(tmp_path / "t.db"))
    from looplens.server.routes import stream_run

    resp = asyncio.run(stream_run("s1", _FakeRequest()))
    assert resp.media_type == "text/event-stream"
