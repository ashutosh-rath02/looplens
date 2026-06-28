"""LoopLens — local-first real-time debugger for AI agent loops.

Public SDK surface (implemented in Phase 2):

    from looplens import trace, event

    with trace("research-agent"):
        event("tool_call_started", tool="web_search", input={"query": "AI agents"})
"""

from __future__ import annotations

__version__ = "0.7.2"

from .sdk import event, flush, observe, trace

__all__ = ["trace", "event", "observe", "flush", "__version__"]
