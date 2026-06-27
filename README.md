# LoopLens

**Chrome DevTools for AI agent loops.** A local-first, real-time debugger that
shows your agent's execution live and warns when it repeats itself, burns
tokens, retries blindly, or stops making progress.

LoopLens gives you:

- live timeline of agent execution
- LLM-call and tool-call visibility
- retry and handoff tracking
- token and cost metrics
- loop warnings (repeated tool, no-progress, retry storm, cost spike, …)
- JSONL import/export
- a local-first UI — no login, no cloud, no API key

## Drop it into any project

LoopLens is **not a standalone app you rebuild your agent inside**. It's a tiny
SDK you add to the agent you already have, plus a dashboard you open when you
want to look.

```python
from looplens import trace, event

with trace("research-agent"):
    event("tool_call_started", tool="web_search", input={"query": "AI agents"})
    event("tool_call_completed", tool="web_search", output={"results": 5})
```

Or wrap a function with `@observe` to capture inputs, outputs, latency, and
errors automatically:

```python
from looplens import observe

@observe(kind="tool")
def web_search(query):
    ...
```

The base install is **pure-stdlib with zero third-party dependencies**, so it
won't conflict with anything in your agent's environment. Events are sent from a
background thread (your loop never blocks). If the dashboard is running, events
stream to it live; if not, the SDK buffers to a local JSONL file and **never
crashes your app**.

Configure via environment variables:

```bash
LOOPLENS_ENDPOINT=http://127.0.0.1:8765   # where the dashboard listens
LOOPLENS_ENABLED=true                      # set false to make the SDK a no-op
LOOPLENS_PROJECT=default
LOOPLENS_CAPTURE_INPUTS=true
LOOPLENS_CAPTURE_OUTPUTS=true
LOOPLENS_TRACE_DIR=looplens-traces         # JSONL fallback location
```

## Install

```bash
pip install looplens             # the SDK (drop into your agent — zero deps)
pip install "looplens[server]"   # adds the dashboard (FastAPI + UI)
```

## Quickstart

```bash
pip install "looplens[server]"
looplens dev      # start backend + UI on http://localhost:8765
looplens demo     # run a sample looping agent that trips a warning
```

## Architecture

```
Your agent app ──(looplens SDK)──▶ Local FastAPI server ──▶ SQLite
                                          │
                                          └──(live stream)──▶ React UI
```

- **SDK** (`looplens`): `trace()` + `event()`, background HTTP send, JSONL
  fallback, fail-silent. Zero third-party deps.
- **Server** (`looplens[server]`): FastAPI + SQLite + Pydantic, loop detectors,
  metrics, real-time stream.
- **UI**: React + Vite + TypeScript + Tailwind.

## Build status

This repo is being built phase by phase (see `PRD.md` section 24).

- [x] **Phase 0** — repo scaffold, packaging, config
- [x] **Phase 1** — FastAPI backend + SQLite + API routes + metrics
- [x] **Phase 2** — Python SDK (`trace` / `event` / `@observe`, background sender, JSONL fallback)
- [x] **Phase 3** — CLI (`init / server / ui / dev / watch / import / export / demo`)
- [x] **Phase 6** — loop detection rules (repeated tool, similar input, no-progress, retry storm, long step, cost spike)
- [x] **Phase 5** — real-time streaming (SSE: live events + metrics + warnings)
- [ ] **Phase 4** — React UI
- [ ] **Phase 7** — polish, examples, demo

## Running the backend today (Phase 1)

```bash
pip install -e ".[server]"
python -m looplens.server        # or: looplens server
curl http://localhost:8765/api/health
# {"status":"healthy","service":"looplens","version":"0.1.0"}
```

Interactive API docs are at `http://localhost:8765/docs`.

## License

MIT
