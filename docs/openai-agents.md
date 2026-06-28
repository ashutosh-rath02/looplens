# OpenAI Agents SDK adapter

The [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) has its
own tracing system — richer than generic OTel spans, with typed spans for
generations, tool calls, **handoffs**, and **guardrails**. This adapter is a
native `TracingProcessor`, so a multi-agent run's handoffs and guardrail trips
are captured directly, with no OTel wiring.

## Setup

```bash
pip install "looplens[openai-agents]"
```

One line:

```python
from looplens.integrations.openai_agents import instrument

instrument(name="my-agents-app")
# ...then use Runner.run(...) / Runner.run_sync(...) as usual.
```

Or register the processor yourself:

```python
from agents.tracing import add_trace_processor
from looplens.integrations.openai_agents import LoopLensTracingProcessor

add_trace_processor(LoopLensTracingProcessor())
```

## What gets mapped

| Agents SDK span | LoopLens event |
| --- | --- |
| Generation / Response | `llm_call_started` / `llm_call_completed` (model, tokens, latency) |
| Function (tool) | `tool_call_started` / `tool_call_completed` (name, input, output) |
| Handoff | `handoff_started` (`agent` = the receiving agent) |
| Agent | `agent_started` / `agent_completed` |
| Guardrail (triggered) | `guardrail_triggered` |
| any span with an error | the `_failed` variant |

Because handoffs are captured natively (not inferred from `transfer_to_*` tool
names), the [`handoff_bounce`](detectors.md) detector fires on agent
oscillation, and guardrail trips show up on the timeline — signals the generic
[OpenTelemetry](opentelemetry.md) path doesn't surface.

!!! note
    One run is tracked at a time (the common sequential case), matching the
    other LoopLens adapters.
