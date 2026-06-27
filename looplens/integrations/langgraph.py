"""LangGraph / LangChain adapter — auto-capture LoopLens events (PRD section 21).

LangGraph runs on LangChain's callback system, so a single ``BaseCallbackHandler``
captures every node's LLM and tool calls without hand-placing ``event()`` calls.
Pass it in the run config::

    from looplens.integrations.langgraph import LoopLensCallbackHandler

    handler = LoopLensCallbackHandler(name="my-graph")
    graph.invoke(inputs, config={"callbacks": [handler]})

Works the same for plain LangChain runnables. Needs ``langchain-core`` (a
LangGraph dependency); install with ``pip install 'looplens[langgraph]'``.

Mapping:
  on_chain_start (root, parent_run_id is None) -> opens a LoopLens run
  on_chain_end / on_chain_error (root)         -> closes it (completed / failed)
  on_llm_start / on_chat_model_start           -> llm_call_started
  on_llm_end                                   -> llm_call_completed (+ tokens, latency)
  on_llm_error                                 -> llm_call_failed
  on_tool_start                                -> tool_call_started (tool + input)
  on_tool_end                                  -> tool_call_completed (+ latency)
  on_tool_error                                -> tool_call_failed
"""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

try:
    from langchain_core.callbacks.base import BaseCallbackHandler
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise ModuleNotFoundError(
        "The LoopLens LangGraph integration needs langchain-core (a LangGraph "
        "dependency).\n\n    pip install 'looplens[langgraph]'\n"
    ) from exc

from ..sdk import _current_run, event, flush, trace


def _first(*values):
    for v in values:
        if v:
            return v
    return None


def _model_name(serialized: dict | None, metadata: dict | None) -> str | None:
    kwargs = (serialized or {}).get("kwargs", {}) if serialized else {}
    return _first(
        (metadata or {}).get("ls_model_name"),
        kwargs.get("model"),
        kwargs.get("model_name"),
    )


def _total_tokens(response: Any) -> int | None:
    # OpenAI-style: response.llm_output["token_usage"]["total_tokens"].
    out = getattr(response, "llm_output", None) or {}
    usage = out.get("token_usage") or out.get("usage") or {}
    total = usage.get("total_tokens")
    if total is not None:
        return total
    # Newer LangChain: usage_metadata on each generation's message.
    summed = 0
    found = False
    for batch in getattr(response, "generations", None) or []:
        for gen in batch:
            meta = getattr(getattr(gen, "message", None), "usage_metadata", None)
            if meta and meta.get("total_tokens") is not None:
                summed += meta["total_tokens"]
                found = True
    return summed if found else None


class LoopLensCallbackHandler(BaseCallbackHandler):
    """LangChain/LangGraph callback handler that streams events to LoopLens.

    One handler instance can be reused across invocations; each ``.invoke()``
    opens a fresh LoopLens run keyed off LangChain's root run id.
    """

    def __init__(self, name: str = "langgraph-agent", *, project: str | None = None):
        self.name = name
        self.project = project
        self._tracer = None
        self._ctx = None
        self._root: UUID | None = None
        self._llm_starts: dict[UUID, float] = {}
        self._tool_starts: dict[UUID, float] = {}
        self._tool_names: dict[UUID, str] = {}

    # --- run lifecycle -----------------------------------------------------

    def _open(self, run_id: UUID) -> None:
        if self._tracer is not None:
            return
        self._tracer = trace(self.name, project=self.project, run_id=f"lg-{run_id}")
        self._ctx = self._tracer.__enter__()  # emits run_started, binds the run
        self._root = run_id

    def _close(self, error: BaseException | None) -> None:
        if self._tracer is None:
            return
        tracer = self._tracer
        self._tracer = self._ctx = self._root = None
        if error is None:
            tracer.__exit__(None, None, None)  # emits run_completed
        else:
            tracer.__exit__(type(error), error, error.__traceback__)  # run_failed
        flush(timeout=2.0)

    def _emit(self, type: str, **kw: Any) -> None:  # noqa: A002
        # Bind to this handler's run even if the callback fires on a worker
        # thread (parallel LangGraph branches), where the trace contextvar set
        # in _open on another thread would not be visible.
        if self._ctx is None:
            event(type, **kw)
            return
        token = _current_run.set(self._ctx)
        try:
            event(type, **kw)
        finally:
            _current_run.reset(token)

    # --- chain (graph / node) ---------------------------------------------

    def on_chain_start(self, serialized, inputs, *, run_id, parent_run_id=None, **kw):
        if parent_run_id is None:
            self._open(run_id)

    def on_chain_end(self, outputs, *, run_id, parent_run_id=None, **kw):
        if run_id == self._root:
            self._close(None)

    def on_chain_error(self, error, *, run_id, parent_run_id=None, **kw):
        if run_id == self._root:
            self._close(error)

    # --- LLM / chat model --------------------------------------------------

    def on_llm_start(self, serialized, prompts, *, run_id, parent_run_id=None,
                     metadata=None, **kw):
        self._llm_starts[run_id] = time.monotonic()
        self._emit("llm_call_started", model=_model_name(serialized, metadata))

    # Chat models (ChatOpenAI, etc.) fire this instead of on_llm_start.
    def on_chat_model_start(self, serialized, messages, *, run_id, parent_run_id=None,
                            metadata=None, **kw):
        self._llm_starts[run_id] = time.monotonic()
        self._emit("llm_call_started", model=_model_name(serialized, metadata))

    def on_llm_end(self, response, *, run_id, parent_run_id=None, **kw):
        start = self._llm_starts.pop(run_id, None)
        latency = int((time.monotonic() - start) * 1000) if start else None
        self._emit("llm_call_completed", tokens=_total_tokens(response),
                   latency_ms=latency)

    def on_llm_error(self, error, *, run_id, parent_run_id=None, **kw):
        start = self._llm_starts.pop(run_id, None)
        latency = int((time.monotonic() - start) * 1000) if start else None
        self._emit("llm_call_failed", latency_ms=latency,
                   error={"message": str(error), "type": type(error).__name__})

    # --- tools -------------------------------------------------------------

    def on_tool_start(self, serialized, input_str, *, run_id, parent_run_id=None,
                      inputs=None, **kw):
        name = (serialized or {}).get("name") or "tool"
        self._tool_starts[run_id] = time.monotonic()
        self._tool_names[run_id] = name
        self._emit("tool_call_started", tool=name, input=inputs or {"input": input_str})

    def on_tool_end(self, output, *, run_id, parent_run_id=None, **kw):
        start = self._tool_starts.pop(run_id, None)
        latency = int((time.monotonic() - start) * 1000) if start else None
        name = self._tool_names.pop(run_id, None)
        self._emit("tool_call_completed", tool=name, latency_ms=latency,
                   output={"result": str(output)})

    def on_tool_error(self, error, *, run_id, parent_run_id=None, **kw):
        start = self._tool_starts.pop(run_id, None)
        latency = int((time.monotonic() - start) * 1000) if start else None
        name = self._tool_names.pop(run_id, None)
        self._emit("tool_call_failed", tool=name, latency_ms=latency,
                   error={"message": str(error), "type": type(error).__name__})
