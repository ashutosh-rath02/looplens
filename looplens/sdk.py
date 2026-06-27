"""LoopLens Python SDK — ``trace()``, ``event()`` and the ``@observe`` decorator.

Design goals (PRD section 14.1 + 23.5):
  * Drop into any agent project — **zero third-party dependencies** (stdlib only).
  * Never block the agent loop — events are sent from a background worker thread.
  * Never crash the host app — every failure is swallowed (set LOOPLENS_DEBUG=1
    to see what went wrong).
  * Work offline — if the server is unreachable, append events to a local JSONL
    file so they can be imported/streamed later.

    from looplens import trace, event

    with trace("research-agent"):
        event("tool_call_started", tool="web_search", input={"query": "AI agents"})
        event("tool_call_completed", tool="web_search", output={"results": 5})
"""

from __future__ import annotations

import atexit
import functools
import json
import os
import queue
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator

from .config import Config, get_config

# Known top-level event fields (PRD section 15.3). Anything else passed to
# event() is folded into `metadata` so nothing is silently dropped.
_EVENT_FIELDS = {
    "agent", "name", "status", "model", "tool", "input", "output", "error",
    "tokens", "cost", "latency_ms", "parent_event_id", "span_id", "trace_id",
    "metadata",
}


# --- run context -----------------------------------------------------------

@dataclass
class _RunCtx:
    run_id: str
    name: str
    project: str
    _seq: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def next_sequence(self) -> int:
        with self._lock:
            self._seq += 1
            return self._seq


_current_run: ContextVar[_RunCtx | None] = ContextVar("looplens_current_run", default=None)
_ambient_run: _RunCtx | None = None  # used when event() is called outside trace()


# --- lazy settings + background sender -------------------------------------

_settings: Config | None = None
_queue: "queue.Queue | None" = None
_worker: threading.Thread | None = None
_start_lock = threading.Lock()

# Circuit breaker: once a send fails we treat the server as down and write
# straight to JSONL, re-probing only every _PROBE_INTERVAL seconds. This keeps
# an offline run from paying the connect timeout on every single event.
_server_down = False
_last_probe = 0.0
_PROBE_INTERVAL = 5.0


def _cfg() -> Config:
    global _settings
    if _settings is None:
        _settings = get_config()
    return _settings


def _debug(msg: str) -> None:
    if _cfg().debug:
        print(f"[looplens] {msg}", file=sys.stderr)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_worker() -> None:
    global _queue, _worker
    if _worker is not None and _worker.is_alive():
        return
    with _start_lock:
        if _worker is not None and _worker.is_alive():
            return
        _queue = queue.Queue()
        _worker = threading.Thread(target=_run_worker, name="looplens-sender", daemon=True)
        _worker.start()
        atexit.register(flush)


def _run_worker() -> None:
    assert _queue is not None
    while True:
        item = _queue.get()
        try:
            if item is None:  # shutdown sentinel
                return
            kind, payload = item
            _deliver(kind, payload)
        except Exception as exc:  # never let the worker die
            _debug(f"worker error: {exc!r}")
        finally:
            _queue.task_done()


def _deliver(kind: str, payload: dict) -> None:
    global _server_down, _last_probe
    cfg = _cfg()

    # Breaker open and not time to re-probe yet: skip HTTP entirely.
    if _server_down and (time.monotonic() - _last_probe) < _PROBE_INTERVAL:
        if kind == "event":
            _write_jsonl(payload)
        return

    path = "/api/runs" if kind == "run" else "/api/events"
    url = cfg.endpoint.rstrip("/") + path
    data = json.dumps(payload, default=str).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    _last_probe = time.monotonic()
    try:
        urllib.request.urlopen(req, timeout=cfg.timeout).close()
        _server_down = False
    except (urllib.error.URLError, OSError) as exc:
        if not _server_down:
            _debug(f"server unreachable ({exc!r}); buffering to JSONL at {cfg.trace_dir}")
        _server_down = True
        if kind == "event":  # run rows are recoverable from the run_started event
            _write_jsonl(payload)


def _write_jsonl(payload: dict) -> None:
    cfg = _cfg()
    try:
        os.makedirs(cfg.trace_dir, exist_ok=True)
        path = os.path.join(cfg.trace_dir, f"{payload['run_id']}.jsonl")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, default=str) + "\n")
    except Exception as exc:  # disk full, permissions, ... — stay silent
        _debug(f"JSONL fallback failed: {exc!r}")


def _enqueue(kind: str, payload: dict) -> None:
    _ensure_worker()
    assert _queue is not None
    _queue.put((kind, payload))


def flush(timeout: float = 3.0) -> None:
    """Block until queued events are delivered (best-effort). Runs at exit."""
    if _queue is None:
        return
    try:
        deadline = time.monotonic() + timeout
        # unfinished_tasks counts in-flight items too (decremented on task_done).
        while _queue.unfinished_tasks > 0 and time.monotonic() < deadline:
            time.sleep(0.02)
    except Exception:
        pass


# --- public API ------------------------------------------------------------

def event(type: str, **kwargs: Any) -> None:  # noqa: A002
    """Emit a single agent event. Safe to call; never raises."""
    try:
        cfg = _cfg()
        if not cfg.enabled:
            return

        run = _current_run.get() or _ambient()
        fields = {k: v for k, v in kwargs.items() if k in _EVENT_FIELDS}
        extra = {k: v for k, v in kwargs.items() if k not in _EVENT_FIELDS}

        if not cfg.capture_inputs:
            fields.pop("input", None)
        if not cfg.capture_outputs:
            fields.pop("output", None)

        metadata = fields.get("metadata") or {}
        if extra:
            metadata = {**metadata, **extra}
        if metadata:
            fields["metadata"] = metadata

        payload = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "run_id": run.run_id,
            "sequence": run.next_sequence(),
            "timestamp": _now(),
            "type": type,
            "project": run.project,
            **fields,
        }
        _enqueue("event", payload)
    except Exception as exc:  # the whole point: don't crash the user's app
        _debug(f"event() error: {exc!r}")


@contextmanager
def trace(name: str, *, project: str | None = None, metadata: dict | None = None,
          run_id: str | None = None) -> Iterator[_RunCtx]:
    """Bracket an agent run. Emits run_started / run_completed (or run_failed)."""
    cfg = _cfg()
    ctx = _RunCtx(
        run_id=run_id or f"run_{uuid.uuid4().hex[:12]}",
        name=name,
        project=project or cfg.project,
    )
    token = _current_run.set(ctx)
    try:
        if cfg.enabled:
            _enqueue("run", {
                "id": ctx.run_id, "name": name, "project": ctx.project,
                "metadata": metadata or {},
            })
            event("run_started", name=name)
        yield ctx
    except BaseException as exc:
        event("run_failed", status="failed", error={"message": str(exc), "type": type(exc).__name__})
        raise
    else:
        event("run_completed", status="completed")
    finally:
        _current_run.reset(token)


def observe(_fn=None, *, name: str | None = None, kind: str = "tool"):
    """Decorator that turns a function call into a started/completed event pair,
    capturing args as input, the return value as output, latency, and errors.

        @observe(kind="tool")
        def web_search(query): ...
    """

    def decorate(fn):
        label = name or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            event(f"{kind}_call_started", name=label, tool=label if kind == "tool" else None,
                  input={"args": list(args), "kwargs": kwargs})
            start = time.monotonic()
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:
                event(f"{kind}_call_failed", name=label,
                      latency_ms=int((time.monotonic() - start) * 1000),
                      error={"message": str(exc), "type": type(exc).__name__})
                raise
            event(f"{kind}_call_completed", name=label,
                  latency_ms=int((time.monotonic() - start) * 1000),
                  output={"result": result})
            return result

        return wrapper

    return decorate if _fn is None else decorate(_fn)


# --- internals -------------------------------------------------------------

def _ambient() -> _RunCtx:
    """Run context for event() calls made outside any trace()."""
    global _ambient_run
    if _ambient_run is None:
        cfg = _cfg()
        _ambient_run = _RunCtx(run_id=f"run_{uuid.uuid4().hex[:12]}", name="ambient",
                               project=cfg.project)
        if cfg.enabled:
            _enqueue("run", {"id": _ambient_run.run_id, "name": "ambient",
                             "project": _ambient_run.project, "metadata": {}})
    return _ambient_run


def _reset_for_tests() -> None:
    """Reset module state (test helper only)."""
    global _settings, _ambient_run, _server_down, _last_probe
    flush()
    _settings = None
    _ambient_run = None
    _server_down = False
    _last_probe = 0.0
