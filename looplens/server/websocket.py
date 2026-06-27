"""Real-time event streaming to the UI (PRD section 14.3 / Phase 5).

NOTE: Implemented in Phase 5. We keep a no-op broadcaster here now so the
ingestion route can announce new events/warnings without later edits. The
transport (WebSocket vs SSE) is decided in Phase 5 — SSE is the likely pick for
a one-directional server→UI stream (auto-reconnect, no upgrade handshake).
"""

from __future__ import annotations

from typing import Any


class Broadcaster:
    """Fan-out hub for live run updates. No-op until Phase 5."""

    async def publish(self, run_id: str, message: dict[str, Any]) -> None:
        return None


broadcaster = Broadcaster()
