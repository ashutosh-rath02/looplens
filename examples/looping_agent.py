"""A stuck agent that calls the same tool over and over (PRD section 27).

Expected LoopLens warnings:
  - Same tool called repeatedly with similar input.
  - Possible no-progress loop detected.

Requires the SDK (Phase 2). Run `looplens dev`, then:
  python examples/looping_agent.py
"""

import time

from looplens import event, trace


def fake_search(query: str) -> None:
    event("tool_call_started", tool="web_search", input={"query": query})
    time.sleep(0.5)
    event("tool_call_completed", tool="web_search", output={"results": []})


with trace("looping-research-agent"):
    event("agent_started", agent="researcher")

    for _ in range(5):
        event("llm_call_started", agent="researcher", model="demo-model")
        time.sleep(0.3)
        event("llm_call_completed", agent="researcher", model="demo-model", tokens=200, cost=0.002)
        fake_search("latest AI agent observability tools")

    event("agent_completed", agent="researcher", status="failed")
