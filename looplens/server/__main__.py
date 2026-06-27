"""Run the backend with ``python -m looplens.server``."""

from __future__ import annotations

from ..config import get_config
from .app import run_server

if __name__ == "__main__":
    cfg = get_config()
    run_server(host=cfg.host, port=cfg.port)
