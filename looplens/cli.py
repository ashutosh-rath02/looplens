"""LoopLens CLI (Typer).

The CLI and dashboard live behind the ``looplens[server]`` extra so the base SDK
install stays dependency-free. We therefore import Typer lazily and show a clear
install hint if it (or the rest of the server stack) is missing.

NOTE: The full command set (init / server / ui / dev / watch / import / export /
demo) lands in Phase 3. For now ``looplens server`` works so the Phase 1 backend
can be exercised through the documented entry point.
"""

from __future__ import annotations

_SERVER_EXTRA_HINT = (
    "The LoopLens CLI and dashboard need extra dependencies.\n\n"
    "    pip install 'looplens[server]'\n"
)


def _build_app():
    import typer

    from .config import get_config

    app = typer.Typer(help="LoopLens — debug AI agent loops.", no_args_is_help=True)

    @app.command()
    def server(
        host: str = typer.Option(None, help="Host to bind (default from config)."),
        port: int = typer.Option(None, help="Port to bind (default from config)."),
    ) -> None:
        """Start the LoopLens FastAPI backend."""
        from .server.app import run_server

        cfg = get_config()
        run_server(host=host or cfg.host, port=port or cfg.port)

    return app


def main() -> None:
    try:
        import typer  # noqa: F401
    except ModuleNotFoundError:
        print(_SERVER_EXTRA_HINT)
        raise SystemExit(1)

    _build_app()()


if __name__ == "__main__":
    main()
