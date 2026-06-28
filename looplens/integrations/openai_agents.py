"""OpenAI Agents SDK adapter — native capture (PRD section 21).

The OpenAI Agents SDK has its own tracing system, richer than generic OTel spans:
it emits typed spans for generations, tool calls, **handoffs**, and **guardrails**.
This adapter is a ``TracingProcessor`` that maps those into LoopLens events, so a
multi-agent run's handoffs and guardrail trips show up natively.

One line to wire it up::

    from looplens.integrations.openai_agents import instrument
    instrument(name="my-agents-app")
    # ...then use Runner.run(...) as usual.

Or register the processor yourself::

    from agents.tracing import add_trace_processor
    from looplens.integrations.openai_agents import LoopLensTracingProcessor
    add_trace_processor(LoopLensTracingProcessor())

Needs the SDK: ``pip install 'looplens[openai-agents]'``.

Mapping:
  on_trace_start                      -> opens a LoopLens run
  on_trace_end                        -> closes it
  Generation / Response span          -> llm_call_started / _completed (+ tokens)
  Function span                       -> tool_call_started / _completed
  Handoff span                        -> handoff_started (agent = to_agent)
  Agent span                          -> agent_started / agent_completed
  Guardrail span (triggered)          -> guardrail_triggered
  any span with an error              -> the *_failed variant

Note: one run is tracked at a time (the common sequential case), matching the
other LoopLens adapters.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

try:
    from agents.tracing import TracingProcessor, add_trace_processor
    from agents.tracing.span_data import (
        AgentSpanData,
        FunctionSpanData,
        GenerationSpanData,
        GuardrailSpanData,
        HandoffSpanData,
        ResponseSpanData,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise ModuleNotFoundError(
        "The LoopLens OpenAI Agents adapter needs the openai-agents SDK.\n\n"
        "    pip install 'looplens[openai-agents]'\n"
    ) from exc

from ..config import get_config
from ..sdk import _current_run, event, flush
from ..sdk import trace as _looplens_trace

_LLM = (GenerationSpanData, ResponseSpanData)


def _model(d: Any) -> str | None:
    m = getattr(d, "model", None)
    if m:
        return m
    resp = getattr(d, "response", None)  # ResponseSpanData carries model on the response
    return getattr(resp, "model", None) if resp else None


def _tokens(d: Any) -> int | None:
    u = getattr(d, "usage", None)
    if not u:
        return None
    get = (lambda k: u.get(k)) if isinstance(u, dict) else (lambda k: getattr(u, k, None))
    total = get("total_tokens")
    if total is not None:
        return total
    prompt = get("input_tokens") or get("prompt_tokens")
    completion = get("output_tokens") or get("completion_tokens")
    if prompt is not None or completion is not None:
        return int(prompt or 0) + int(completion or 0)
    return None


def _latency_ms(span: Any) -> int | None:
    def parse(v):
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                return None
        return None

    s, e = parse(getattr(span, "started_at", None)), parse(getattr(span, "ended_at", None))
    return int((e - s).total_seconds() * 1000) if s and e else None


def _error(span: Any) -> dict | None:
    err = getattr(span, "error", None)
    if not err:
        return None
    if isinstance(err, dict):
        return {"message": err.get("message") or str(err), "type": "error"}
    return {"message": str(err), "type": type(err).__name__}


class LoopLensTracingProcessor(TracingProcessor):
    """Streams OpenAI Agents SDK trace spans to LoopLens."""

    def __init__(self, name: str = "openai-agents", *, project: str | None = None):
        self.name = name
        self.project = project
        self._cm = None
        self._ctx = None

    # --- run lifecycle -----------------------------------------------------

    def on_trace_start(self, trace: Any) -> None:
        self._cm = _looplens_trace(
            getattr(trace, "name", None) or self.name,
            project=self.project,
            run_id=f"agents-{getattr(trace, 'trace_id', '')}",
        )
        self._ctx = self._cm.__enter__()  # emits run_started, binds the run

    def on_trace_end(self, trace: Any) -> None:
        cm = self._cm
        self._cm = self._ctx = None
        if cm is not None:
            try:
                cm.__exit__(None, None, None)  # emits run_completed
            except Exception:
                pass
        flush(timeout=2.0)

    def _emit(self, type: str, **kw: Any) -> None:  # noqa: A002
        if self._ctx is None:
            event(type, **kw)
            return
        token = _current_run.set(self._ctx)
        try:
            event(type, **kw)
        finally:
            _current_run.reset(token)

    # --- spans -------------------------------------------------------------

    def on_span_start(self, span: Any) -> None:
        d = span.span_data
        if isinstance(d, _LLM):
            self._emit("llm_call_started", model=_model(d))
        elif isinstance(d, FunctionSpanData):
            self._emit("tool_call_started", tool=d.name, input={"value": d.input})
        elif isinstance(d, HandoffSpanData):
            # The handoff *is* the transition; emit once, on start.
            self._emit("handoff_started", agent=d.to_agent,
                       metadata={"from": d.from_agent})
        elif isinstance(d, AgentSpanData):
            self._emit("agent_started", agent=d.name)

    def on_span_end(self, span: Any) -> None:
        d = span.span_data
        err = _error(span)
        latency = _latency_ms(span)
        if isinstance(d, _LLM):
            if err:
                self._emit("llm_call_failed", model=_model(d), latency_ms=latency, error=err)
            else:
                self._emit("llm_call_completed", model=_model(d), tokens=_tokens(d),
                           latency_ms=latency)
        elif isinstance(d, FunctionSpanData):
            if err:
                self._emit("tool_call_failed", tool=d.name, latency_ms=latency, error=err)
            else:
                self._emit("tool_call_completed", tool=d.name, latency_ms=latency,
                           output={"value": d.output})
        elif isinstance(d, GuardrailSpanData):
            if getattr(d, "triggered", False):
                self._emit("guardrail_triggered", name=d.name)
        elif isinstance(d, AgentSpanData):
            self._emit("agent_completed", agent=d.name)

    def force_flush(self) -> None:
        flush(timeout=2.0)

    def shutdown(self) -> None:
        self.on_trace_end(None)


def instrument(name: str = "openai-agents", *, project: str | None = None) -> LoopLensTracingProcessor:
    """Register a LoopLens processor with the Agents SDK and return it."""
    processor = LoopLensTracingProcessor(name=name, project=project)
    add_trace_processor(processor)
    return processor
