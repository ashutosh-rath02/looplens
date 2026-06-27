"""Tests for the universal OpenTelemetry ingestion path (POST /v1/traces).

Spans are posted as OTLP/JSON (no extra dep) and the assertions go through the
real API, so this exercises the whole map -> store -> detect -> metrics pipeline.
"""

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


def _attr(key, **value):
    return {"key": key, "value": value}


def _span(trace, span, name, kind, start, end, *, parent="", extra=None):
    attrs = [_attr("openinference.span.kind", stringValue=kind)] if kind else []
    attrs += extra or []
    return {
        "traceId": trace, "spanId": span, "parentSpanId": parent, "name": name,
        "startTimeUnixNano": str(start), "endTimeUnixNano": str(end),
        "attributes": attrs, "status": {},
    }


def _post(client, spans):
    payload = {"resourceSpans": [{"scopeSpans": [{"spans": spans}]}]}
    return client.post("/v1/traces", content=json.dumps(payload),
                       headers={"content-type": "application/json"})


def test_openinference_spans_become_run_events_and_warnings(client):
    trace = "a" * 32
    root = "a" * 16
    spans = [_span(trace, root, "research-agent", "CHAIN", 1000, 9000)]
    spans.append(_span(trace, "b" * 16, "chat", "LLM", 1100, 1500, parent=root, extra=[
        _attr("llm.model_name", stringValue="gpt-4o-mini"),
        _attr("llm.token_count.total", intValue="42"),
    ]))
    for i in range(4):  # the same tool, same input -> a loop
        spans.append(_span(trace, f"{i:016x}", "search", "TOOL", 2000 + i * 100,
                           2050 + i * 100, parent=root, extra=[
                               _attr("tool.name", stringValue="search"),
                               _attr("input.value", stringValue="same query"),
                           ]))

    r = _post(client, spans)
    assert r.status_code == 200, r.text

    rid = "otel-" + trace
    assert any(x["id"] == rid for x in client.get("/api/runs").json())
    events = client.get(f"/api/runs/{rid}/events").json()
    types = [e["type"] for e in events]
    assert types.count("tool_call_started") == 4
    assert "llm_call_started" in types and "llm_call_completed" in types

    metrics = client.get(f"/api/runs/{rid}/metrics").json()
    assert metrics["total_tokens"] == 42
    assert metrics["loop_health_status"] != "Healthy"

    warns = {w["type"] for w in client.get(f"/api/runs/{rid}/warnings").json()}
    assert "repeated_tool_call" in warns
    assert "repeated_tool_call_exact_input" in warns


def test_genai_semconv_is_recognized_without_openinference_kind(client):
    # No openinference.span.kind — kind must be inferred from gen_ai.* attributes.
    trace = "b" * 32
    root = "c" * 16
    spans = [_span(trace, root, "agent", None, 10, 300)]
    spans.append(_span(trace, "d" * 16, "chat gpt-4o", None, 20, 80, parent=root, extra=[
        _attr("gen_ai.operation.name", stringValue="chat"),
        _attr("gen_ai.request.model", stringValue="gpt-4o"),
        _attr("gen_ai.usage.input_tokens", intValue="10"),
        _attr("gen_ai.usage.output_tokens", intValue="5"),
    ]))
    spans.append(_span(trace, "e" * 16, "execute_tool", None, 90, 150, parent=root, extra=[
        _attr("gen_ai.tool.name", stringValue="lookup"),
        _attr("input.value", stringValue="q"),
    ]))

    assert _post(client, spans).status_code == 200
    rid = "otel-" + trace
    events = client.get(f"/api/runs/{rid}/events").json()
    assert "llm_call_started" in [e["type"] for e in events]
    assert any(e["type"] == "tool_call_started" and e["tool"] == "lookup" for e in events)
    assert client.get(f"/api/runs/{rid}/metrics").json()["total_tokens"] == 15


def test_unrecognized_spans_are_skipped_not_errored(client):
    # A retriever/embedding span we don't map should be ignored, not 500.
    trace = "f" * 32
    spans = [_span(trace, "f" * 16, "vectorstore", "RETRIEVER", 1, 5)]
    assert _post(client, spans).status_code == 200
    rid = "otel-" + trace
    assert client.get(f"/api/runs/{rid}/events").json() == []


def test_late_arriving_root_corrects_run_name(client):
    # SimpleSpanProcessor exports children before the root finishes. The child
    # batch names the run after a child; the later root batch must fix it.
    trace = "1" * 32
    root = "1" * 16
    child = _span(trace, "2" * 16, "ChatCompletion", "LLM", 20, 80, parent=root)
    assert _post(client, [child]).status_code == 200
    rid = "otel-" + trace
    assert next(r for r in client.get("/api/runs").json() if r["id"] == rid)["name"] == "ChatCompletion"

    # Root arrives in a later export.
    assert _post(client, [_span(trace, root, "research-agent", "CHAIN", 10, 200)]).status_code == 200
    run = next(r for r in client.get("/api/runs").json() if r["id"] == rid)
    assert run["name"] == "research-agent"
    assert run["status"] == "completed"


def test_transfer_tool_spans_trip_handoff_bounce(client):
    # Alternating transfer_to_* tool spans are an agent handoff bounce.
    trace = "9" * 32
    root = "9" * 16
    spans = [_span(trace, root, "swarm", "CHAIN", 1, 100)]
    names = ["transfer_to_researcher", "transfer_to_planner",
             "transfer_to_researcher", "transfer_to_planner"]
    for i, nm in enumerate(names):
        spans.append(_span(trace, f"{i:016x}", nm, "TOOL", 10 + i, 12 + i, parent=root,
                           extra=[_attr("tool.name", stringValue=nm)]))

    assert _post(client, spans).status_code == 200
    rid = "otel-" + trace
    warns = {w["type"] for w in client.get(f"/api/runs/{rid}/warnings").json()}
    assert "handoff_bounce" in warns
    metrics = client.get(f"/api/runs/{rid}/metrics").json()
    assert metrics["total_handoffs"] == 4


def test_otlp_protobuf_path(client):
    pb = pytest.importorskip("opentelemetry.proto.collector.trace.v1.trace_service_pb2")
    req = pb.ExportTraceServiceRequest()
    sp = req.resource_spans.add().scope_spans.add().spans.add()
    sp.trace_id = bytes.fromhex("cc" * 16)
    sp.span_id = bytes.fromhex("dd" * 8)
    sp.name = "search"
    sp.start_time_unix_nano = 1000
    sp.end_time_unix_nano = 2000
    kind = sp.attributes.add(); kind.key = "openinference.span.kind"; kind.value.string_value = "TOOL"
    tname = sp.attributes.add(); tname.key = "tool.name"; tname.value.string_value = "search"

    r = client.post("/v1/traces", content=req.SerializeToString(),
                    headers={"content-type": "application/x-protobuf"})
    assert r.status_code == 200, r.text
    rid = "otel-" + "cc" * 16
    assert any(e["type"] == "tool_call_started" for e in client.get(f"/api/runs/{rid}/events").json())
