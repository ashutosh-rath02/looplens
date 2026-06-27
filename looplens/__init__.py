"""LoopLens — local-first real-time debugger for AI agent loops.

Public SDK surface (implemented in Phase 2):

    from looplens import trace, event

    with trace("research-agent"):
        event("tool_call_started", tool="web_search", input={"query": "AI agents"})
"""

from __future__ import annotations

__version__ = "0.1.0"

from .sdk import event, trace

__all__ = ["trace", "event", "__version__"]
