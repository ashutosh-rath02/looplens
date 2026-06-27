"""LoopLens configuration, sourced from environment variables.

Shared by the SDK (where to send events) and the server (where to listen and
store). See PRD section 14.1 for the documented environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Config:
    # SDK: where to send events, and capture toggles.
    endpoint: str = "http://localhost:8765"
    enabled: bool = True
    project: str = "default"
    capture_inputs: bool = True
    capture_outputs: bool = True

    # Server: where to listen and where SQLite lives.
    host: str = "127.0.0.1"
    port: int = 8765
    db_path: str = "looplens.db"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            endpoint=os.environ.get("LOOPLENS_ENDPOINT", "http://localhost:8765"),
            enabled=_as_bool(os.environ.get("LOOPLENS_ENABLED"), True),
            project=os.environ.get("LOOPLENS_PROJECT", "default"),
            capture_inputs=_as_bool(os.environ.get("LOOPLENS_CAPTURE_INPUTS"), True),
            capture_outputs=_as_bool(os.environ.get("LOOPLENS_CAPTURE_OUTPUTS"), True),
            host=os.environ.get("LOOPLENS_HOST", "127.0.0.1"),
            port=int(os.environ.get("LOOPLENS_PORT", "8765")),
            db_path=os.environ.get("LOOPLENS_DB_PATH", "looplens.db"),
        )


def get_config() -> Config:
    """Read configuration fresh from the environment."""
    return Config.from_env()
