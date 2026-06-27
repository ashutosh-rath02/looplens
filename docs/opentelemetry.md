# OpenTelemetry ingestion

This is the **universal** path: any framework that can emit OpenTelemetry spans
streams into LoopLens with **no LoopLens code in your agent**. The server exposes
an OTLP/HTTP receiver at `POST /v1/traces`; point your existing OTel exporter at
it and the spans become LoopLens runs, events, and loop warnings.

## Setup

```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(endpoint="http://127.0.0.1:8765/v1/traces")
# register it on your TracerProvider, then instrument your framework as usual
```

Or configure it with the standard environment variables — no code at all:

```bash
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:8765/v1/traces
```

Then start the dashboard (`looplens dev`) and run your agent.

## Install

OTLP/JSON works with the base server and **no extra dependency**. The common
default wire format, OTLP/protobuf, needs the `otel` extra:

```bash
pip install "looplens[otel]"
```

If a protobuf request arrives without the extra installed, the endpoint replies
`415` with a hint (or export OTLP/JSON via `OTEL_EXPORTER_OTLP_PROTOCOL=http/json`).

## What gets mapped

LoopLens is deliberately lenient and reads whichever semantic convention a span
uses — `openinference.*`, `traceloop.*`, `gen_ai.*`, or `llm.*`:

| Span | Becomes | Fields captured |
| --- | --- | --- |
| LLM / chat-model span | `llm_call_started` + `llm_call_completed` | model, token counts, latency, input/output |
| Tool span | `tool_call_started` + `tool_call_completed` | tool name, input/output, latency |
| Span with error status | the `_failed` variant | error message |
| Root span (no parent) | the **run** | run name, start/end, completed/failed status |

One trace becomes one run. Because exporters often flush child spans before the
root finishes, a late-arriving root span corrects the run's name and status.
Span kinds LoopLens doesn't map (retriever, embedding, …) are skipped, not
errored.

## Example

`examples/otel_openinference_openai.py` captures a real OpenAI call through
OpenInference's auto-instrumentation — three lines of OTel setup, then your code
runs untouched:

```bash
pip install 'looplens[otel]' opentelemetry-sdk \
    opentelemetry-exporter-otlp-proto-http \
    openinference-instrumentation-openai openai
export OPENAI_API_KEY=sk-...
looplens dev
PYTHONPATH=. python examples/otel_openinference_openai.py
```

The same three-line setup works for the OpenInference / OpenLLMetry
instrumentations of LangChain, LlamaIndex, CrewAI, AutoGen, and others — LoopLens
just ingests the spans.

!!! note "Handoffs"
    The OTel mapper captures LLM and tool spans today, not yet agent/node
    transitions, so the [`handoff_bounce`](detectors.md) detector won't fire
    through this path. Mapping agent-span transitions to handoff events is on
    the [roadmap](roadmap.md).
