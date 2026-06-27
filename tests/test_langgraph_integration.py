"""Tests for the LangGraph/LangChain callback adapter.

These drive the handler with synthetic LangChain callback arguments and record
the LoopLens events it emits, so no real graph, LLM, or server is needed. The
SDK transport (trace/event/flush) is stubbed to keep the mapping under test.
"""

from __future__ import annotations

import contextlib
from uuid import uuid4

import pytest

pytest.importorskip("langchain_core")  # the adapter import needs langchain-core

from looplens.integrations import langgraph as lg  # noqa: E402


@pytest.fixture
def recorder(monkeypatch):
    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(lg, "event", lambda type, **kw: events.append((type, kw)))
    monkeypatch.setattr(lg, "flush", lambda *a, **k: None)

    @contextlib.contextmanager
    def fake_trace(name, *, project=None, run_id=None):
        events.append(("run_started", {"name": name, "run_id": run_id}))
        try:
            yield object()
        except BaseException:
            events.append(("run_failed", {}))
            raise
        else:
            events.append(("run_completed", {}))

    monkeypatch.setattr(lg, "trace", fake_trace)
    return events


def types(events):
    return [t for t, _ in events]


def test_happy_path_maps_llm_and_tool_calls(recorder):
    h = lg.LoopLensCallbackHandler(name="g")
    root, llm, tool = uuid4(), uuid4(), uuid4()

    h.on_chain_start({}, {}, run_id=root, parent_run_id=None)
    h.on_chat_model_start({"kwargs": {"model": "gpt-4o-mini"}}, [], run_id=llm, parent_run_id=root)
    resp = type("R", (), {"llm_output": {"token_usage": {"total_tokens": 42}}, "generations": []})()
    h.on_llm_end(resp, run_id=llm, parent_run_id=root)
    h.on_tool_start({"name": "search"}, "kittens", run_id=tool, parent_run_id=root)
    h.on_tool_end("no results", run_id=tool, parent_run_id=root)
    h.on_chain_end({}, run_id=root, parent_run_id=None)

    assert types(recorder) == [
        "run_started", "llm_call_started", "llm_call_completed",
        "tool_call_started", "tool_call_completed", "run_completed",
    ]
    by = {t: kw for t, kw in recorder}
    assert by["llm_call_started"]["model"] == "gpt-4o-mini"
    assert by["llm_call_completed"]["tokens"] == 42
    assert by["tool_call_started"]["tool"] == "search"


def test_only_root_chain_opens_and_closes_the_run(recorder):
    # Nested node chains (parent_run_id set) must not open/close extra runs.
    h = lg.LoopLensCallbackHandler()
    root, node = uuid4(), uuid4()
    h.on_chain_start({}, {}, run_id=root, parent_run_id=None)
    h.on_chain_start({}, {}, run_id=node, parent_run_id=root)  # a node, ignored
    h.on_chain_end({}, run_id=node, parent_run_id=root)        # node end, ignored
    h.on_chain_end({}, run_id=root, parent_run_id=None)
    assert types(recorder) == ["run_started", "run_completed"]


def test_tool_error_maps_to_failed(recorder):
    h = lg.LoopLensCallbackHandler()
    root, tool = uuid4(), uuid4()
    h.on_chain_start({}, {}, run_id=root, parent_run_id=None)
    h.on_tool_start({"name": "charge"}, "x", run_id=tool, parent_run_id=root)
    h.on_tool_error(ValueError("boom"), run_id=tool, parent_run_id=root)
    assert "tool_call_failed" in types(recorder)


def test_chain_error_closes_run_as_failed(recorder):
    h = lg.LoopLensCallbackHandler()
    root = uuid4()
    h.on_chain_start({}, {}, run_id=root, parent_run_id=None)
    h.on_chain_error(RuntimeError("graph blew up"), run_id=root, parent_run_id=None)
    assert types(recorder) == ["run_started", "run_failed"]
