"""CrewAI adapter — native capture (PRD section 21).

CrewAI emits typed events on its global event bus. This adapter is a
``BaseEventListener`` that maps them to LoopLens events, including **crew
delegation**: when control passes to a different agent, it emits
``handoff_started``, so ``handoff_bounce`` fires when a crew gets stuck
ping-ponging between two agents (something the generic OTel path can't recover,
since CrewAI's delegation target lives in tool *arguments*, not the tool name).

One line to wire it up::

    from looplens.integrations.crewai import instrument
    instrument(name="my-crew")
    # ...then crew.kickoff() as usual.

Needs CrewAI: ``pip install 'looplens[crewai]'``.

Mapping:
  CrewKickoffStarted / Completed / Failed -> opens / closes the run
  LLMCallStarted / Completed / Failed     -> llm_call_started / _completed / _failed
  ToolUsageStarted / Finished / Error      -> tool_call_started / _completed / _failed
  AgentExecutionStarted                    -> agent_started (+ handoff_started on agent change)
  AgentExecutionCompleted                  -> agent_completed
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

try:
    from crewai.events import (
        AgentExecutionCompletedEvent,
        AgentExecutionStartedEvent,
        CrewKickoffCompletedEvent,
        CrewKickoffFailedEvent,
        CrewKickoffStartedEvent,
        LLMCallCompletedEvent,
        LLMCallFailedEvent,
        LLMCallStartedEvent,
        ToolUsageErrorEvent,
        ToolUsageFinishedEvent,
        ToolUsageStartedEvent,
    )
    from crewai.events.base_event_listener import BaseEventListener
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise ModuleNotFoundError(
        "The LoopLens CrewAI adapter needs the crewai package.\n\n"
        "    pip install 'looplens[crewai]'\n"
    ) from exc

from ..sdk import _current_run, event, flush
from ..sdk import trace as _looplens_trace


def _tokens(usage: Any) -> int | None:
    if not usage:
        return None
    get = (lambda k: usage.get(k)) if isinstance(usage, dict) else (lambda k: getattr(usage, k, None))
    total = get("total_tokens")
    if total is not None:
        return total
    prompt = get("prompt_tokens") or get("input_tokens")
    completion = get("completion_tokens") or get("output_tokens")
    if prompt is not None or completion is not None:
        return int(prompt or 0) + int(completion or 0)
    return None


def _agent(ev: Any) -> str | None:
    return getattr(ev, "agent_role", None) or getattr(ev, "from_agent", None)


def _latency(ev: Any) -> int | None:
    s, e = getattr(ev, "started_at", None), getattr(ev, "finished_at", None)
    if isinstance(s, datetime) and isinstance(e, datetime):
        return int((e - s).total_seconds() * 1000)
    return None


class LoopLensEventListener(BaseEventListener):
    """Streams CrewAI bus events to LoopLens."""

    def __init__(self, name: str = "crewai", *, project: str | None = None):
        self.name = name
        self.project = project
        self._cm = None
        self._ctx = None
        self._last_agent: str | None = None
        super().__init__()  # registers the handlers below on the global bus

    # --- run lifecycle -----------------------------------------------------

    def _on_kickoff_start(self, ev: Any) -> None:
        self._last_agent = None
        self._cm = _looplens_trace(
            getattr(ev, "crew_name", None) or self.name,
            project=self.project,
            run_id=f"crewai-{uuid.uuid4().hex[:12]}",
        )
        self._ctx = self._cm.__enter__()

    def _on_kickoff_end(self, error: Any) -> None:
        cm = self._cm
        self._cm = self._ctx = None
        self._last_agent = None
        if cm is not None:
            try:
                if error:
                    cm.__exit__(RuntimeError, RuntimeError(str(error)), None)  # -> run_failed
                else:
                    cm.__exit__(None, None, None)  # -> run_completed
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

    # --- handlers ----------------------------------------------------------

    def _h_agent_start(self, ev: Any) -> None:
        role = _agent(ev)
        if role and self._last_agent and role != self._last_agent:
            self._emit("handoff_started", agent=role)  # control passed to a new agent
        if role:
            self._emit("agent_started", agent=role)
            self._last_agent = role

    def _h_agent_completed(self, ev: Any) -> None:
        self._emit("agent_completed", agent=_agent(ev))

    def _h_llm_start(self, ev: Any) -> None:
        self._emit("llm_call_started", model=getattr(ev, "model", None), agent=_agent(ev))

    def _h_llm_completed(self, ev: Any) -> None:
        self._emit("llm_call_completed", model=getattr(ev, "model", None),
                   tokens=_tokens(getattr(ev, "usage", None)), agent=_agent(ev))

    def _h_llm_failed(self, ev: Any) -> None:
        self._emit("llm_call_failed", error={"message": str(getattr(ev, "error", ""))})

    def _h_tool_start(self, ev: Any) -> None:
        self._emit("tool_call_started", tool=getattr(ev, "tool_name", None),
                   input={"args": getattr(ev, "tool_args", None)}, agent=_agent(ev))

    def _h_tool_finished(self, ev: Any) -> None:
        self._emit("tool_call_completed", tool=getattr(ev, "tool_name", None),
                   output={"value": getattr(ev, "output", None)}, latency_ms=_latency(ev),
                   agent=_agent(ev))

    def _h_tool_error(self, ev: Any) -> None:
        self._emit("tool_call_failed", tool=getattr(ev, "tool_name", None),
                   error={"message": str(getattr(ev, "error", ""))})

    def setup_listeners(self, bus: Any) -> None:
        wiring = [
            (CrewKickoffStartedEvent, lambda s, e: self._on_kickoff_start(e)),
            (CrewKickoffCompletedEvent, lambda s, e: self._on_kickoff_end(None)),
            (CrewKickoffFailedEvent, lambda s, e: self._on_kickoff_end(getattr(e, "error", "crew failed"))),
            (LLMCallStartedEvent, lambda s, e: self._h_llm_start(e)),
            (LLMCallCompletedEvent, lambda s, e: self._h_llm_completed(e)),
            (LLMCallFailedEvent, lambda s, e: self._h_llm_failed(e)),
            (ToolUsageStartedEvent, lambda s, e: self._h_tool_start(e)),
            (ToolUsageFinishedEvent, lambda s, e: self._h_tool_finished(e)),
            (ToolUsageErrorEvent, lambda s, e: self._h_tool_error(e)),
            (AgentExecutionStartedEvent, lambda s, e: self._h_agent_start(e)),
            (AgentExecutionCompletedEvent, lambda s, e: self._h_agent_completed(e)),
        ]
        for event_type, handler in wiring:
            bus.on(event_type)(handler)


def instrument(name: str = "crewai", *, project: str | None = None) -> LoopLensEventListener:
    """Register a LoopLens listener on the CrewAI event bus and return it."""
    return LoopLensEventListener(name=name, project=project)
