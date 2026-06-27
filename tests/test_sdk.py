"""Tests for the LoopLens SDK's offline/resilience behavior (Phase 2).

These run without a live server: the endpoint points at a dead port so the
circuit breaker trips and events are buffered to JSONL.
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys

import pytest

import looplens
from looplens import sdk


def _dead_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def offline(tmp_path, monkeypatch):
    traces = tmp_path / "traces"
    monkeypatch.setenv("LOOPLENS_ENDPOINT", f"http://127.0.0.1:{_dead_port()}")
    monkeypatch.setenv("LOOPLENS_TRACE_DIR", str(traces))
    monkeypatch.setenv("LOOPLENS_TIMEOUT", "0.3")
    monkeypatch.setenv("LOOPLENS_DEBUG", "0")
    sdk._reset_for_tests()
    yield traces
    sdk._reset_for_tests()


def test_import_pulls_in_no_third_party_packages():
    """`import looplens` must not import the server stack (zero-dep SDK)."""
    code = (
        "import looplens, sys;"
        "heavy={'fastapi','pydantic','uvicorn','typer','starlette','watchdog'};"
        "bad=heavy & {m.split('.')[0] for m in sys.modules};"
        "print('OK' if not bad else 'BAD:' + ','.join(sorted(bad)))"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.stdout.strip() == "OK", out.stdout + out.stderr


def test_offline_buffers_events_to_jsonl(offline):
    from looplens import event, trace

    with trace("t"):
        event("llm_call_started", model="m")
        event("custom_note", foo="bar")  # extra kwarg -> metadata
    looplens.flush(timeout=5)

    files = list(offline.glob("*.jsonl"))
    assert len(files) == 1
    lines = [json.loads(line) for line in files[0].read_text().splitlines()]
    assert [e["type"] for e in lines] == [
        "run_started", "llm_call_started", "custom_note", "run_completed",
    ]
    assert [e["sequence"] for e in lines] == [1, 2, 3, 4]
    custom = next(e for e in lines if e["type"] == "custom_note")
    assert custom["metadata"] == {"foo": "bar"}


def test_observe_decorator_emits_started_and_completed(offline):
    from looplens import observe, trace

    @observe(kind="tool")
    def search(q):
        return {"hits": 0}

    with trace("t"):
        search("hello")
    looplens.flush(timeout=5)

    lines = [json.loads(x) for x in next(offline.glob("*.jsonl")).read_text().splitlines()]
    types = [e["type"] for e in lines]
    assert "tool_call_started" in types
    assert "tool_call_completed" in types


def test_never_raises_when_server_down(offline):
    from looplens import event, trace

    # Must not raise even though nothing is listening.
    with trace("t"):
        event("anything")
    looplens.flush(timeout=5)


def test_disabled_is_a_noop(tmp_path, monkeypatch):
    traces = tmp_path / "traces"
    monkeypatch.setenv("LOOPLENS_ENABLED", "false")
    monkeypatch.setenv("LOOPLENS_TRACE_DIR", str(traces))
    monkeypatch.setenv("LOOPLENS_ENDPOINT", f"http://127.0.0.1:{_dead_port()}")
    sdk._reset_for_tests()

    from looplens import event, trace

    with trace("t"):
        event("y")
    looplens.flush(timeout=2)

    assert not traces.exists()
    sdk._reset_for_tests()
