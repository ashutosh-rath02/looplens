"""OpenTelemetry trace ingestion — the universal framework path (PRD section 21).

Most agent frameworks (LangChain/LangGraph, LlamaIndex, CrewAI, AutoGen, the
OpenAI Agents SDK, ...) can emit OpenTelemetry spans via the OpenInference or
OpenLLMetry instrumentations. Point their OTLP/HTTP exporter at this server's
``/v1/traces`` endpoint and LoopLens maps the spans into its own event model, so
the loop detectors, metrics, and live UI work with zero LoopLens-specific code.

We are deliberately lenient: we read whichever of the common semantic
conventions a span happens to use (``openinference.*``, ``traceloop.*``,
``gen_ai.*``, ``llm.*``) and skip spans we don't recognise rather than failing.

Two wire formats are supported on ``/v1/traces``:
  * OTLP/JSON     (``application/json``)        — parsed with the stdlib.
  * OTLP/protobuf (``application/x-protobuf``)  — needs ``opentelemetry-proto``
    (``pip install 'looplens[otel]'``); imported lazily.
"""

from __future__ import annotations

import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from . import db
from .detectors import run_detectors
from .ingest import store_event

# Handoffs are conventionally expressed as `transfer_to_<agent>` tool calls
# (LangGraph supervisor/swarm, CrewAI delegation). Detecting that — not every
# tool — keeps a normal ReAct loop from looking like an agent bounce.
_HANDOFF_RE = re.compile(r"^(?:transfer|handoff)(?:_back)?_to_(.+)$", re.IGNORECASE)


def _handoff_target(tool_name: str | None) -> str | None:
    if not tool_name:
        return None
    m = _HANDOFF_RE.match(tool_name)
    return m.group(1) if m else None


# --- wire-format parsing ---------------------------------------------------

def _g(d: dict, *keys: str, default=None):
    """First present key (handles camelCase vs snake_case across exporters)."""
    for k in keys:
        if k in d:
            return d[k]
    return default


def _json_anyvalue(v: dict) -> Any:
    """Decode an OTLP/JSON AnyValue."""
    if not isinstance(v, dict):
        return v
    if "stringValue" in v or "string_value" in v:
        return _g(v, "stringValue", "string_value")
    if "intValue" in v or "int_value" in v:
        return int(_g(v, "intValue", "int_value"))
    if "doubleValue" in v or "double_value" in v:
        return float(_g(v, "doubleValue", "double_value"))
    if "boolValue" in v or "bool_value" in v:
        return bool(_g(v, "boolValue", "bool_value"))
    if "arrayValue" in v or "array_value" in v:
        arr = _g(v, "arrayValue", "array_value") or {}
        return [_json_anyvalue(x) for x in arr.get("values", [])]
    if "kvlistValue" in v or "kvlist_value" in v:
        kv = _g(v, "kvlistValue", "kvlist_value") or {}
        return {e["key"]: _json_anyvalue(e["value"]) for e in kv.get("values", [])}
    return None


def _json_attrs(attributes: list[dict]) -> dict[str, Any]:
    return {a["key"]: _json_anyvalue(a.get("value", {})) for a in attributes or []}


def _status_code(status: Any) -> int:
    # JSON encodes the enum as a name ("STATUS_CODE_ERROR") or an int; 2 == error.
    if isinstance(status, dict):
        code = _g(status, "code", default=0)
        if isinstance(code, str):
            return 2 if code.endswith("ERROR") else (1 if code.endswith("OK") else 0)
        return int(code or 0)
    return 0


def parse_otlp_json(body: dict) -> list[dict]:
    """Normalise an OTLP/JSON ExportTraceServiceRequest into flat span dicts."""
    spans: list[dict] = []
    for rs in _g(body, "resourceSpans", "resource_spans", default=[]) or []:
        for ss in _g(rs, "scopeSpans", "scope_spans", default=[]) or []:
            for sp in _g(ss, "spans", default=[]) or []:
                spans.append({
                    "trace_id": _g(sp, "traceId", "trace_id", default=""),
                    "span_id": _g(sp, "spanId", "span_id", default=""),
                    "parent_span_id": _g(sp, "parentSpanId", "parent_span_id", default=""),
                    "name": _g(sp, "name", default=""),
                    "start_ns": int(_g(sp, "startTimeUnixNano", "start_time_unix_nano", default=0) or 0),
                    "end_ns": int(_g(sp, "endTimeUnixNano", "end_time_unix_nano", default=0) or 0),
                    "status_code": _status_code(_g(sp, "status", default={})),
                    "attrs": _json_attrs(_g(sp, "attributes", default=[])),
                })
    return spans


def parse_otlp_protobuf(data: bytes) -> list[dict]:
    """Normalise an OTLP/protobuf request. Needs the optional ``otel`` extra."""
    try:
        from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
            ExportTraceServiceRequest,
        )
        from opentelemetry.proto.common.v1.common_pb2 import AnyValue
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised via the route
        raise _MissingProto() from exc

    def anyval(v: "AnyValue") -> Any:
        kind = v.WhichOneof("value")
        if kind == "string_value":
            return v.string_value
        if kind == "int_value":
            return v.int_value
        if kind == "double_value":
            return v.double_value
        if kind == "bool_value":
            return v.bool_value
        if kind == "array_value":
            return [anyval(x) for x in v.array_value.values]
        if kind == "kvlist_value":
            return {kv.key: anyval(kv.value) for kv in v.kvlist_value.values}
        return None

    req = ExportTraceServiceRequest()
    req.ParseFromString(data)
    spans: list[dict] = []
    for rs in req.resource_spans:
        for ss in rs.scope_spans:
            for sp in ss.spans:
                spans.append({
                    "trace_id": sp.trace_id.hex(),
                    "span_id": sp.span_id.hex(),
                    "parent_span_id": sp.parent_span_id.hex(),
                    "name": sp.name,
                    "start_ns": sp.start_time_unix_nano,
                    "end_ns": sp.end_time_unix_nano,
                    "status_code": int(sp.status.code),
                    "attrs": {kv.key: anyval(kv.value) for kv in sp.attributes},
                })
    return spans


class _MissingProto(RuntimeError):
    """Raised when OTLP/protobuf arrives but ``opentelemetry-proto`` isn't installed."""


# --- span -> LoopLens semantics --------------------------------------------

_LLM_OPS = {"chat", "completion", "text_completion", "generate_content", "embeddings"}


def _span_kind(attrs: dict, name: str) -> str | None:
    kind = attrs.get("openinference.span.kind")
    if kind:
        return str(kind).upper()
    tl = attrs.get("traceloop.span.kind")
    if tl:
        return {"llm": "LLM", "tool": "TOOL", "agent": "AGENT",
                "task": "CHAIN", "workflow": "CHAIN"}.get(str(tl).lower(), str(tl).upper())
    if attrs.get("gen_ai.operation.name") in _LLM_OPS:
        return "LLM"
    if attrs.get("tool.name") or attrs.get("gen_ai.tool.name"):
        return "TOOL"
    if "llm.model_name" in attrs or "gen_ai.request.model" in attrs:
        return "LLM"
    return None


def _model(attrs: dict) -> str | None:
    return _g(attrs, "llm.model_name", "gen_ai.response.model", "gen_ai.request.model",
              "gen_ai.system")


def _tokens(attrs: dict) -> int | None:
    total = _g(attrs, "llm.token_count.total", "gen_ai.usage.total_tokens")
    if total is not None:
        return int(total)
    prompt = _g(attrs, "llm.token_count.prompt", "gen_ai.usage.input_tokens",
                "gen_ai.usage.prompt_tokens")
    completion = _g(attrs, "llm.token_count.completion", "gen_ai.usage.output_tokens",
                    "gen_ai.usage.completion_tokens")
    if prompt is not None or completion is not None:
        return int(prompt or 0) + int(completion or 0)
    return None


def _tool_name(attrs: dict, name: str) -> str:
    return _g(attrs, "tool.name", "gen_ai.tool.name") or name or "tool"


def _value(attrs: dict, *keys: str):
    raw = _g(attrs, *keys)
    return {"value": raw} if raw is not None else None


def _iso(ns: int) -> str:
    return datetime.fromtimestamp((ns or 0) / 1e9, tz=timezone.utc).isoformat()


def _true_root(spans: list[dict]) -> dict | None:
    """The span with no parent. None if this batch holds only child spans (they
    can be exported before the root span finishes)."""
    roots = [s for s in spans if not s.get("parent_span_id")]
    return min(roots, key=lambda s: s["start_ns"]) if roots else None


def _events_for_span(run_id: str, sp: dict) -> list[tuple[int, dict]]:
    """Return (sort_ns, store_event-kwargs) pairs for one span. LLM/TOOL spans
    become a started/completed (or _failed) pair; other spans contribute none."""
    attrs, name = sp["attrs"], sp["name"]
    kind = _span_kind(attrs, name)
    if kind not in ("LLM", "TOOL"):
        return []

    base = {"run_id": run_id, "span_id": sp["span_id"], "trace_id": sp["trace_id"],
            "name": name, "detect": False}
    errored = sp["status_code"] == 2
    latency = int((sp["end_ns"] - sp["start_ns"]) / 1e6) if sp["end_ns"] else None
    out: list[tuple[int, dict]] = []

    if kind == "LLM":
        out.append((sp["start_ns"], {**base, "type": "llm_call_started", "model": _model(attrs),
                                     "input": _value(attrs, "input.value")}))
        done = {**base, "model": _model(attrs), "tokens": _tokens(attrs),
                "latency_ms": latency, "output": _value(attrs, "output.value")}
        if errored:
            out.append((sp["end_ns"], {**done, "type": "llm_call_failed",
                                       "error": {"message": name, "type": "error"}}))
        else:
            out.append((sp["end_ns"], {**done, "type": "llm_call_completed"}))
    else:  # TOOL
        tool = _tool_name(attrs, name)
        out.append((sp["start_ns"], {**base, "type": "tool_call_started", "tool": tool,
                                     "input": _value(attrs, "input.value", "tool.parameters")}))
        target = _handoff_target(tool)
        if target:
            out.append((sp["start_ns"], {**base, "type": "handoff_started", "agent": target}))
        done = {**base, "tool": tool, "latency_ms": latency,
                "output": _value(attrs, "output.value")}
        if errored:
            out.append((sp["end_ns"], {**done, "type": "tool_call_failed",
                                       "error": {"message": name, "type": "error"}}))
        else:
            out.append((sp["end_ns"], {**done, "type": "tool_call_completed"}))
    return out


def ingest_spans(conn: sqlite3.Connection, spans: list[dict]) -> list[str]:
    """Map normalised spans into runs+events. One trace -> one run. Returns the
    run ids touched. Detection runs once per run after all spans are stored."""
    by_trace: dict[str, list[dict]] = defaultdict(list)
    for sp in spans:
        if sp.get("trace_id"):
            by_trace[sp["trace_id"]].append(sp)

    touched: list[str] = []
    for trace_id, group in by_trace.items():
        group.sort(key=lambda s: s["start_ns"])
        root = _true_root(group)
        anchor = root or group[0]  # name/start from the root if present, else earliest
        run_id = f"otel-{trace_id}"
        db.create_run(conn, id=run_id, name=anchor["name"] or trace_id[:8],
                      project="default", started_at=_iso(anchor["start_ns"]))

        pairs: list[tuple[int, dict]] = []
        for sp in group:
            pairs.extend(_events_for_span(run_id, sp))
        pairs.sort(key=lambda p: p[0])
        for _ts, kwargs in pairs:
            store_event(conn, timestamp=_iso(_ts), **kwargs)

        run_detectors(conn, run_id)
        # The root span often finishes (and exports) after its children, so when
        # it finally arrives, correct the run's name/start and close it out.
        if root:
            db.set_run_name(conn, run_id, root["name"] or trace_id[:8], _iso(root["start_ns"]))
            if root["end_ns"]:
                status = "failed" if root["status_code"] == 2 else "completed"
                db.set_run_status(conn, run_id, status, _iso(root["end_ns"]))
        touched.append(run_id)
    return touched
