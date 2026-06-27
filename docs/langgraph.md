# LangGraph / LangChain adapter

For a tight, in-process integration with LangGraph or LangChain, drop in the
LoopLens callback handler. LangGraph runs on LangChain's callback system, so a
single handler captures every node's LLM and tool calls — no manual `event()`
calls.

## Setup

```bash
pip install "looplens[langgraph]"
```

```python
from looplens.integrations.langgraph import LoopLensCallbackHandler

handler = LoopLensCallbackHandler(name="my-graph")
graph.invoke(inputs, config={"callbacks": [handler]})   # that's the whole change
```

One handler instance can be reused across invocations; each `.invoke()` opens a
fresh LoopLens run keyed off LangChain's root run id. Works the same for plain
LangChain runnables and for `.ainvoke()`.

## What gets mapped

| LangChain callback | LoopLens event |
| --- | --- |
| `on_chat_model_start` / `on_llm_start` | `llm_call_started` (with model) |
| `on_llm_end` | `llm_call_completed` (with token counts, latency) |
| `on_llm_error` | `llm_call_failed` |
| `on_tool_start` | `tool_call_started` (tool name, input) |
| `on_tool_end` | `tool_call_completed` (latency) |
| `on_tool_error` | `tool_call_failed` |
| root chain start / end | opens / closes the run |

Each emit is bound to the handler's run via the trace context, so even
parallel-branch callbacks that fire on worker threads land on the right run.

## Example

`examples/langgraph_agent.py` is a real LangGraph ReAct agent, auto-instrumented
with zero manual `event()` calls:

```bash
pip install "looplens[langgraph]" langchain-openai
export OPENAI_API_KEY=sk-...
looplens dev
PYTHONPATH=. python examples/langgraph_agent.py
```

!!! note "Handoffs"
    `transfer_to_<agent>` tool calls (the LangGraph supervisor/swarm handoff
    convention) are also emitted as `handoff_started` events, so the
    [`handoff_bounce`](detectors.md) detector fires when agents ping-pong. A
    normal ReAct `agent`↔`tools` loop is **not** treated as a handoff.
