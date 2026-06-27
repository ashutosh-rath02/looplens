"""A minimal healthy agent — one LLM call, one tool call, done.

Requires the SDK (Phase 2):  pip install -e .
Run the dashboard first:      looplens dev
Then:                          python examples/simple_agent.py
"""

from looplens import event, trace

with trace("simple-agent"):
    event("agent_started", agent="assistant")
    event("llm_call_started", agent="assistant", model="demo-model")
    event("llm_call_completed", agent="assistant", model="demo-model", tokens=420, cost=0.004)
    event("tool_call_started", tool="web_search", input={"query": "weather in Tokyo"})
    event("tool_call_completed", tool="web_search", output={"results": 3})
    event("agent_completed", agent="assistant", status="success")
