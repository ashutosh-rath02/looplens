# Examples

Runnable agents live under [`examples/`](https://github.com/ashutosh-rath02/looplens/tree/main/examples)
in the repo. Start the dashboard (`looplens dev`), then run any of them.

## Zero-dependency demos

These use only the base SDK — no API key, no extra installs:

```bash
python examples/simple_agent.py          # a healthy run — no warnings
python examples/looping_agent.py         # repeated tool call + no-progress loop
python examples/retry_storm_agent.py     # retry storm
python examples/handoff_bounce_agent.py  # two agents ping-ponging handoffs
```

`looplens demo` runs the looping agent without needing the file checked out.

## Real agents

These make live LLM calls and genuinely loop, so you see real detection on real
data.

### `real_research_agent_openai.py`

A raw OpenAI Chat Completions function-calling agent. Its `search` tool covers a
tiny corpus that lacks the answer, so the model keeps searching.

```bash
pip install openai
OPENAI_API_KEY=sk-... PYTHONPATH=. python examples/real_research_agent_openai.py
```

### `langgraph_agent.py`

The same idea with **zero manual instrumentation** — a real LangGraph ReAct agent
captured through the [LangGraph adapter](langgraph.md).

```bash
pip install "looplens[langgraph]" langchain-openai
OPENAI_API_KEY=sk-... PYTHONPATH=. python examples/langgraph_agent.py
```

### `otel_openinference_openai.py`

A real OpenAI call captured through [OpenTelemetry](opentelemetry.md) — no
LoopLens code in the agent, just an OTLP exporter pointed at the server.

```bash
pip install "looplens[otel]" opentelemetry-sdk \
    opentelemetry-exporter-otlp-proto-http \
    openinference-instrumentation-openai openai
OPENAI_API_KEY=sk-... PYTHONPATH=. python examples/otel_openinference_openai.py
```
