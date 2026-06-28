# CrewAI adapter

CrewAI emits typed events on a global event bus. This adapter is a
`BaseEventListener` that maps them to LoopLens events — including **crew
delegation**: when control passes to a different agent it emits
`handoff_started`, so [`handoff_bounce`](detectors.md) fires when a crew gets
stuck ping-ponging between two agents. (The generic [OpenTelemetry](opentelemetry.md)
path can't recover this, because CrewAI's delegation *target* lives in the tool
arguments, not the tool name.)

## Setup

```bash
pip install "looplens[crewai]"
```

One line:

```python
from looplens.integrations.crewai import instrument

instrument(name="my-crew")
# ...then crew.kickoff() as usual.
```

## What gets mapped

| CrewAI event | LoopLens event |
| --- | --- |
| Crew kickoff started / completed / failed | opens / closes the run |
| LLM call started / completed / failed | `llm_call_started` / `llm_call_completed` (tokens) / `llm_call_failed` |
| Tool usage started / finished / error | `tool_call_started` / `tool_call_completed` (latency) / `tool_call_failed` |
| Agent execution started | `agent_started`, plus `handoff_started` when the executing agent **changes** |
| Agent execution completed | `agent_completed` |

A handoff is emitted only when control moves to a *different* agent, so a single
agent looping on its own task is **not** mistaken for a bounce — only a real
two-agent ping-pong trips `handoff_bounce`.

!!! note
    CrewAI is a heavy dependency and isn't part of LoopLens's CI; this adapter is
    verified locally. One run is tracked at a time (the common sequential case).
