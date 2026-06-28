"""Tests for the OpenAI Agents SDK adapter.

Drives the TracingProcessor with synthetic trace/span objects (the SDK's real
span_data dataclasses wrapped in lightweight fakes) and records the LoopLens
events it emits. No live agent run or server needed.
"""

from __future__ import annotations

import contextlib

import pytest

pytest.importorskip("agents")

from agents.tracing import span_data as sd  # noqa: E402

from looplens.integrations import openai_agents as oa  # noqa: E402


class FakeSpan:
    def __init__(self, span_data, *, error=None, started_at=None, ended_at=None, trace_id="t1"):
        self.span_data = span_data
        self.error = error
        self.started_at = started_at
        self.ended_at = ended_at
        self.trace_id = trace_id
        self.span_id = "s"
        self.parent_id = None


class FakeTrace:
    def __init__(self, trace_id="t1", name="workflow"):
        self.trace_id = trace_id
        self.name = name


@pytest.fixture
def recorder(monkeypatch):
    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(oa, "event", lambda type, **kw: events.append((type, kw)))
    monkeypatch.setattr(oa, "flush", lambda *a, **k: None)

    @contextlib.contextmanager
    def fake_trace(name, *, project=None, run_id=None):
        events.append(("run_started", {"name": name, "run_id": run_id}))
        try:
            yield object()
        finally:
            events.append(("run_completed", {}))

    monkeypatch.setattr(oa, "_looplens_trace", fake_trace)
    return events


def types(events):
    return [t for t, _ in events]


def test_maps_generation_tool_and_handoff(recorder):
    p = oa.LoopLensTracingProcessor(name="app")
    p.on_trace_start(FakeTrace(name="research-workflow"))

    gen = sd.GenerationSpanData(model="gpt-4o", usage={"total_tokens": 50})
    p.on_span_start(FakeSpan(gen))
    p.on_span_end(FakeSpan(gen, started_at="2026-01-01T00:00:00", ended_at="2026-01-01T00:00:01"))

    fn = sd.FunctionSpanData(name="search", input="q", output="r")
    p.on_span_start(FakeSpan(fn))
    p.on_span_end(FakeSpan(fn))

    ho = sd.HandoffSpanData(from_agent="planner", to_agent="researcher")
    p.on_span_start(FakeSpan(ho))
    p.on_span_end(FakeSpan(ho))  # handoff emits only on start

    p.on_trace_end(FakeTrace())

    assert types(recorder) == [
        "run_started", "llm_call_started", "llm_call_completed",
        "tool_call_started", "tool_call_completed", "handoff_started", "run_completed",
    ]
    by = {t: kw for t, kw in recorder}
    assert by["run_started"]["name"] == "research-workflow"
    assert by["llm_call_started"]["model"] == "gpt-4o"
    assert by["llm_call_completed"]["tokens"] == 50
    assert by["llm_call_completed"]["latency_ms"] == 1000
    assert by["tool_call_started"]["tool"] == "search"
    assert by["handoff_started"]["agent"] == "researcher"


def test_guardrail_and_tool_error(recorder):
    p = oa.LoopLensTracingProcessor()
    p.on_trace_start(FakeTrace())

    g = sd.GuardrailSpanData(name="no_pii", triggered=True)
    p.on_span_start(FakeSpan(g))  # nothing on start for a guardrail
    p.on_span_end(FakeSpan(g))

    fn = sd.FunctionSpanData(name="charge", input="x", output=None)
    p.on_span_start(FakeSpan(fn))
    p.on_span_end(FakeSpan(fn, error={"message": "boom"}))

    p.on_trace_end(FakeTrace())

    seq = types(recorder)
    assert "guardrail_triggered" in seq
    assert "tool_call_failed" in seq
    assert "tool_call_completed" not in seq  # the errored tool must not also complete