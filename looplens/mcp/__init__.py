"""LoopLens MCP server package.

Exposes LoopLens loop-health data over the Model Context Protocol (MCP) so an
AI coding agent — Claude Code, Cursor, Windsurf, … — can ask *"did my last
agent run loop, and where do I fix it?"* without leaving the editor.

It is **read-only**: it reads the same local SQLite store the dashboard and SDK
already populate, so there is no separate capture path and no new product
surface — just the existing loop verdicts, surfaced as MCP tools.

    pip install "looplens[mcp]"
    looplens mcp

The heavy ``mcp`` dependency is imported lazily inside :func:`build_mcp`, so
importing this package is cheap and never fails when the extra isn't installed.
"""

from __future__ import annotations

from .server import build_mcp, run_mcp

__all__ = ["build_mcp", "run_mcp"]
