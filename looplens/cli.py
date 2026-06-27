"""LoopLens CLI (Typer).

The CLI and dashboard live behind the ``looplens[server]`` extra so the base SDK
install stays dependency-free. Typer is therefore imported lazily, with a clear
install hint if it is missing.

Commands (PRD section 14.2):
  init    server    ui    dev    watch    import    export    demo    doctor
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .config import get_config

_SERVER_EXTRA_HINT = (
    "The LoopLens CLI and dashboard need extra dependencies.\n\n"
    "    pip install 'looplens[server]'\n"
)


# --- small HTTP helpers (used by import/watch/export) ----------------------

def _post(endpoint: str, path: str, payload: dict, timeout: float) -> bool:
    url = endpoint.rstrip("/") + path
    data = json.dumps(payload, default=str).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        urllib.request.urlopen(req, timeout=timeout).close()
        return True
    except (urllib.error.URLError, OSError):
        return False


def _get(endpoint: str, path: str, timeout: float):
    url = endpoint.rstrip("/") + path
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.load(resp)


def _ingest_line(endpoint: str, line: str, timeout: float, seen_runs: set[str]) -> bool:
    line = line.strip()
    if not line:
        return False
    try:
        evt = json.loads(line)
    except json.JSONDecodeError:
        return False
    run_id = evt.get("run_id")
    # Recreate the run with its real name the first time we see it.
    if run_id and run_id not in seen_runs:
        seen_runs.add(run_id)
        name = evt.get("name") if evt.get("type") == "run_started" else run_id
        _post(endpoint, "/api/runs", {"id": run_id, "name": name or run_id,
                                      "project": evt.get("project", "default")}, timeout)
    return _post(endpoint, "/api/events", evt, timeout)


# --- demo agent ------------------------------------------------------------

def _run_demo() -> None:
    import time

    from .sdk import event, trace

    with trace("looping-research-agent"):
        event("agent_started", agent="researcher")
        for _ in range(5):
            event("llm_call_started", agent="researcher", model="demo-model")
            time.sleep(0.3)
            event("llm_call_completed", agent="researcher", model="demo-model",
                  tokens=200, cost=0.002)
            event("tool_call_started", tool="web_search",
                  input={"query": "latest AI agent observability tools"})
            time.sleep(0.3)
            event("tool_call_completed", tool="web_search", output={"results": []})
        event("agent_completed", agent="researcher", status="failed")


# --- app -------------------------------------------------------------------

def _build_app():
    import typer

    app = typer.Typer(help="LoopLens — debug AI agent loops.", no_args_is_help=True)

    @app.command()
    def init() -> None:
        """Create a local config template and the JSONL fallback dir."""
        cfg = get_config()
        Path(cfg.trace_dir).mkdir(parents=True, exist_ok=True)
        env_file = Path("looplens.env")
        if not env_file.exists():
            env_file.write_text(
                "# LoopLens configuration. Export these (or `source looplens.env`).\n"
                f"LOOPLENS_ENDPOINT={cfg.endpoint}\n"
                "LOOPLENS_ENABLED=true\n"
                f"LOOPLENS_PROJECT={cfg.project}\n"
                "LOOPLENS_CAPTURE_INPUTS=true\n"
                "LOOPLENS_CAPTURE_OUTPUTS=true\n"
                f"LOOPLENS_TRACE_DIR={cfg.trace_dir}\n"
                f"LOOPLENS_DB_PATH={cfg.db_path}\n",
                encoding="utf-8",
            )
            typer.echo(f"Wrote {env_file}")
        else:
            typer.echo(f"{env_file} already exists; left unchanged")
        typer.echo(f"Trace dir: {cfg.trace_dir}")
        typer.echo(f"Endpoint:  {cfg.endpoint}")

    @app.command()
    def server(
        host: str = typer.Option(None, help="Host to bind (default from config)."),
        port: int = typer.Option(None, help="Port to bind (default from config)."),
    ) -> None:
        """Start the LoopLens FastAPI backend."""
        from .server.app import run_server

        cfg = get_config()
        run_server(host=host or cfg.host, port=port or cfg.port)

    @app.command()
    def ui() -> None:
        """Start the React dev server (UI is built in Phase 4)."""
        if not Path("ui/package.json").exists():
            typer.echo("UI is not built yet (Phase 4). Run `looplens server` for the API.")
            raise typer.Exit(code=0)
        import subprocess

        subprocess.run(["npm", "--prefix", "ui", "run", "dev"], check=False)

    @app.command()
    def dev(
        host: str = typer.Option(None, help="Host to bind (default from config)."),
        port: int = typer.Option(None, help="Port to bind (default from config)."),
        open_browser: bool = typer.Option(
            True, "--open/--no-open", help="Open the dashboard in a browser once the server starts."
        ),
    ) -> None:
        """Start the backend (and, from a source checkout, the UI dev server)."""
        import subprocess
        import threading
        import webbrowser

        cfg = get_config()
        bind_host = host or cfg.host
        bind_port = port or cfg.port
        ui_proc = None
        if Path("ui/package.json").exists():
            # Source checkout: Vite serves a hot-reloading UI that proxies to the backend.
            ui_proc = subprocess.Popen(["npm", "--prefix", "ui", "run", "dev"])
            url = "http://localhost:5173"
        else:
            # Installed package: the backend serves the bundled UI on its own port.
            shown_host = "127.0.0.1" if bind_host in ("0.0.0.0", "") else bind_host
            url = f"http://{shown_host}:{bind_port}"
        if open_browser:
            # run_server blocks, so open the page from a timer once it has come up.
            threading.Timer(1.5, lambda: webbrowser.open(url)).start()
        try:
            from .server.app import run_server

            run_server(host=bind_host, port=bind_port)
        finally:
            if ui_proc is not None:
                ui_proc.terminate()

    @app.command(name="import")
    def import_(file: str = typer.Argument(..., help="JSONL trace file to import.")) -> None:
        """Import a JSONL trace file into the dashboard."""
        cfg = get_config()
        path = Path(file)
        if not path.exists():
            typer.echo(f"No such file: {file}")
            raise typer.Exit(code=1)
        seen: set[str] = set()
        ok = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if _ingest_line(cfg.endpoint, line, cfg.timeout, seen):
                ok += 1
        typer.echo(f"Imported {ok} events from {file} into {len(seen)} run(s).")

    @app.command()
    def export(
        run_id: str = typer.Argument(..., help="Run id to export."),
        output: str = typer.Option(None, "--output", "-o", help="Write to file (default stdout)."),
    ) -> None:
        """Export one run's events as JSONL."""
        cfg = get_config()
        try:
            events = _get(cfg.endpoint, f"/api/runs/{run_id}/events", cfg.timeout)
        except (urllib.error.URLError, OSError) as exc:
            typer.echo(f"Could not reach server at {cfg.endpoint}: {exc}")
            raise typer.Exit(code=1)
        lines = "\n".join(json.dumps(e, default=str) for e in events)
        if output:
            Path(output).write_text(lines + "\n", encoding="utf-8")
            typer.echo(f"Wrote {len(events)} events to {output}")
        else:
            typer.echo(lines)

    @app.command()
    def watch(directory: str = typer.Argument("traces", help="Directory of JSONL files to stream.")) -> None:
        """Watch a directory of JSONL trace files and stream them into LoopLens."""
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        cfg = get_config()
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        offsets: dict[str, int] = {}
        seen: set[str] = set()

        def pump(path: Path) -> None:
            if path.suffix != ".jsonl":
                return
            start = offsets.get(str(path), 0)
            with path.open("r", encoding="utf-8") as fh:
                fh.seek(start)
                for line in fh:
                    _ingest_line(cfg.endpoint, line, cfg.timeout, seen)
                offsets[str(path)] = fh.tell()

        for existing in root.glob("*.jsonl"):
            pump(existing)

        class _Handler(FileSystemEventHandler):
            def on_modified(self, e):
                if not e.is_directory:
                    pump(Path(e.src_path))

            on_created = on_modified

        obs = Observer()
        obs.schedule(_Handler(), str(root), recursive=False)
        obs.start()
        typer.echo(f"Watching {root}/ for JSONL traces (Ctrl+C to stop)...")
        try:
            while True:
                obs.join(1)
        except KeyboardInterrupt:
            obs.stop()
        obs.join()

    @app.command()
    def demo() -> None:
        """Run a sample looping agent that intentionally repeats a tool call."""
        cfg = get_config()
        typer.echo(f"Running demo agent -> {cfg.endpoint}")
        typer.echo("(start `looplens dev` first to watch it live)")
        _run_demo()
        from .sdk import flush

        flush(timeout=5)
        typer.echo("Demo complete. Open the dashboard to inspect the run.")

    @app.command()
    def doctor() -> None:
        """Diagnose setup: server reachability, SDK round-trip, JSONL fallback."""
        import uuid

        cfg = get_config()
        ok = True
        typer.echo(f"LoopLens doctor - endpoint {cfg.endpoint}")

        # 1) Is the dashboard server up and healthy?
        server_up = False
        health: dict = {}
        try:
            health = _get(cfg.endpoint, "/api/health", cfg.timeout)
            server_up = health.get("status") == "healthy"
        except (urllib.error.URLError, OSError):
            server_up = False
        if server_up:
            typer.echo(f"  [ok]   server reachable (version {health.get('version', '?')})")
        else:
            ok = False
            typer.echo("  [FAIL] server not reachable - start it with `looplens dev`")

        # 2) SDK -> server round-trip (only meaningful once the server is up).
        if server_up:
            if not cfg.enabled:
                typer.echo("  [warn] LOOPLENS_ENABLED=false - SDK is a no-op; skipped round-trip")
            else:
                from .sdk import event, flush, trace

                rid = f"looplens-doctor-{uuid.uuid4().hex[:8]}"
                with trace("looplens doctor self-test", run_id=rid):
                    event("tool_call_started", tool="__doctor__", input={"ping": True})
                    event("tool_call_completed", tool="__doctor__")
                flush(timeout=5)
                try:
                    events = _get(cfg.endpoint, f"/api/runs/{rid}/events", cfg.timeout)
                except (urllib.error.URLError, OSError):
                    events = []
                if events:
                    typer.echo(f"  [ok]   SDK round-trip - {len(events)} events delivered (run {rid})")
                else:
                    ok = False
                    typer.echo("  [FAIL] SDK round-trip - events were not delivered")

        # 3) JSONL fallback dir is writable (the SDK buffers here when offline).
        try:
            trace_dir = Path(cfg.trace_dir)
            trace_dir.mkdir(parents=True, exist_ok=True)
            probe = trace_dir / ".doctor-write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            typer.echo(f"  [ok]   JSONL fallback writable ({trace_dir})")
        except OSError as exc:
            ok = False
            typer.echo(f"  [FAIL] JSONL fallback not writable ({cfg.trace_dir}): {exc}")

        typer.echo("All checks passed." if ok else "Some checks failed.")
        raise typer.Exit(code=0 if ok else 1)

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
