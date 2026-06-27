"""Test the SSE live stream (Phase 5) via FastAPI's TestClient."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LOOPLENS_DB_PATH", str(tmp_path / "t.db"))
    from looplens.server.app import app

    with TestClient(app) as c:
        yield c


def test_sse_streams_snapshot_and_warnings(client):
    client.post("/api/runs", json={"id": "s1", "name": "s"})
    # A tiny loop so the stream also carries a warning.
    client.post("/api/events", json={"run_id": "s1", "type": "run_started"})
    for _ in range(3):
        client.post("/api/events", json={"run_id": "s1", "type": "retry_triggered", "tool": "x"})

    with client.stream("GET", "/api/runs/s1/stream") as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        count = 0
        for line in r.iter_lines():
            count += 1
            if count > 40:
                pytest.fail("no update frame received")
            if line.startswith("data:"):
                data = json.loads(line[len("data:"):])
                if data.get("type") == "update":
                    types = {e["type"] for e in data["events"]}
                    assert "run_started" in types
                    assert any(w["type"] == "retry_storm" for w in data["warnings"])
                    assert data["metrics"]["total_events"] >= 4
                    break
