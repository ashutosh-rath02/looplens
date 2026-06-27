"""Two agents that hand off back and forth without resolving (PRD §17 Rule 7).

Models a real multi-agent failure mode seen in CrewAI / LangGraph-style setups:
a planner delegates to a researcher, the researcher kicks it back to the planner,
and neither ever finishes — control just ping-pongs (planner -> researcher ->
planner -> researcher) burning tokens.

Expected LoopLens warning:
  - Possible handoff bounce detected.

Requires the SDK (Phase 2). Run `looplens dev`, then:
  python examples/handoff_bounce_agent.py
"""

import time

from looplens import event, trace

with trace("handoff-bounce-agent"):
    event("agent_started", agent="planner")

    # `agent` on handoff_started is the agent receiving control.
    for _ in range(4):
        event("llm_call_started", agent="planner", model="demo-model")
        time.sleep(0.2)
        event("llm_call_completed", agent="planner", model="demo-model", tokens=180, cost=0.0018)
        event("handoff_started", agent="researcher", metadata={"from": "planner"})

        event("llm_call_started", agent="researcher", model="demo-model")
        time.sleep(0.2)
        event("llm_call_completed", agent="researcher", model="demo-model", tokens=180, cost=0.0018)
        event("handoff_started", agent="planner", metadata={"from": "researcher"})

    event("agent_completed", agent="planner", status="failed")
