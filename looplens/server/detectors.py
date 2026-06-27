"""Loop detection rules (PRD section 17).

NOTE: The six detectors (repeated tool, similar input, no-progress, retry storm,
long-running step, cost spike) are implemented in Phase 6. This module already
exposes the stable entry point the ingestion route calls on every event, so
wiring does not change when the rules land.
"""

from __future__ import annotations

import sqlite3


def run_detectors(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    """Return a list of newly-raised warning rows for ``run_id``.

    Phase 1: no rules yet, so nothing is raised.
    """
    return []
