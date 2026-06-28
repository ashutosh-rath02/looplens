"""Tests for the CrewAI adapter.

CrewAI is a heavy dependency, so it is not installed in CI — these run locally
where ``crewai`` is available (skipped otherwise). They drive the listener's
handler methods directly with fake bus events and record the LoopLens events
emitted, with the SDK transport stubbed.
"""

from __future__ import annotations

import contextlib

import pytest

pytest.importorskip("crewai")

from looplens.integrations import crewai as cr  # noqa: E402


class FakeEv:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


@pytest.fixture
def recorder(monkeypatch):
    events: list[tuple[str, dict]] = []
    monkeypatch.setattr(cr, "event", lambda type, **kw: events.append((type, kw)))
    monkeypatch.setattr(cr, "flush", lambda *a, **k: None)

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

    monkeypatch.setattr(cr, "_looplens_trace", fake_trace)
    return events


def types(events):
    return [t for t, _ in events]


def test_maps_llm_and_tool_events(recorder):
    listener = cr.LoopLensEventListener(name="crew")
    listener._on_kickoff_start(FakeEv(crew_name="research-crew"))
    listener._h_llm_start(FakeEv(model="gpt-4o", agent_role="researcher"))
    listener._h_llm_completed(FakeEv(model="gpt-4o", usage={"total_tokens": 80}, agent_role="researcher"))
    listener._h_tool_start(FakeEv(tool_name="search", tool_args={"q": "x"}, agent_role="researcher"))
    listener._h_tool_finished(FakeEv(tool_name="search", output="no results"))
    listener._on_kickoff_end(None)

    assert types(recorder) == [
        "run_started", "llm_call_started", "llm_call_completed",
        "tool_call_started", "tool_call_completed", "run_completed",
    ]
    by = {t: kw for t, kw in recorder}
    assert by["run_started"]["name"] == "research-crew"
    assert by["llm_call_started"]["model"] == "gpt-4o"
    assert by["llm_call_completed"]["tokens"] == 80
    assert by["tool_call_started"]["tool"] == "search"


def test_delegation_emits_handoff_on_agent_change(recorder):
    listener = cr.LoopLensEventListener()
    listener._on_kickoff_start(FakeEv(crew_name="crew"))
    for role in ["manager", "researcher", "manager", "researcher"]:
        listener._h_agent_start(FakeEv(agent_role=role))
    listener._on_kickoff_end(None)

    # The first agent isn't a handoff; each subsequent change is.
    handoffs = [kw["agent"] for t, kw in recorder if t == "handoff_started"]
    assert handoffs == ["researcher", "manager", "researcher"]
    agents = [kw["agent"] for t, kw in recorder if t == "agent_started"]
    assert agents == ["manager", "researcher", "manager", "researcher"]


def test_same_agent_repeating_is_not_a_handoff(recorder):
    listener = cr.LoopLensEventListener()
    listener._on_kickoff_start(FakeEv(crew_name="crew"))
    for _ in range(3):
        listener._h_agent_start(FakeEv(agent_role="solo"))
    listener._on_kickoff_end(None)
    assert "handoff_started" not in types(recorder)


def test_failed_kickoff_closes_run_as_failed(recorder):
    listener = cr.LoopLensEventListener()
    listener._on_kickoff_start(FakeEv(crew_name="crew"))
    listener._on_kickoff_end("boom")
    assert types(recorder) == ["run_started", "run_failed"]
