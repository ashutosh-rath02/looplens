"""An agent that retries a failing tool without changing strategy.

Expected LoopLens warning:
  - Retry storm detected.

Requires the SDK (Phase 2). Run `looplens dev`, then:
  python examples/retry_storm_agent.py
"""

import time

from looplens import event, trace

with trace("retry-storm-agent"):
    event("agent_started", agent="worker")

    for attempt in range(4):
        event("tool_call_started", tool="charge_card", input={"amount": 42})
        time.sleep(0.2)
        event("tool_call_failed", tool="charge_card", error={"message": "gateway timeout"})
        event("retry_triggered", tool="charge_card", metadata={"attempt": attempt + 1})

    event("agent_completed", agent="worker", status="failed")
