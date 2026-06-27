# Architecture

LoopLens is a single local process plus a tiny SDK. Everything stays on
`127.0.0.1` — no login, no cloud, no API key.

```
Your agent app ──(looplens SDK / OTel / adapter)──▶ Local FastAPI server ──▶ SQLite
                                                            │
                                                            └──(live stream)──▶ React UI
```

## Components

- **SDK** (`looplens`): `trace()` + `event()` + `@observe`, a background HTTP
  sender, and a JSONL fallback. Zero third-party dependencies; fail-silent.
- **Server** (`looplens[server]`): FastAPI + SQLite + Pydantic. Hosts the ingest
  API, the loop detectors, metrics, the SSE live stream, and the
  [OpenTelemetry receiver](opentelemetry.md) at `/v1/traces`.
- **UI**: React + Vite + TypeScript + Tailwind, prebuilt and bundled into the
  wheel so installing the `[server]` extra needs no Node.

## Ingestion pipeline

Every event — whether it came from the SDK (`POST /api/events`), an OTel exporter
(`POST /v1/traces`), or a JSONL import — funnels through one shared `store_event`
path. That path writes the event, updates run totals and lifecycle, runs the
[loop detectors](detectors.md), and feeds the live stream. So detection, scoring,
and the UI behave identically no matter how an agent was instrumented.

## Storage

SQLite with three tables — `runs`, `events`, `warnings` — opened per operation
with WAL enabled. Metrics and health are computed on demand from the stored
events and warnings, so there's no derived state to keep in sync.

## Data flow characteristics

- **Near-real-time, not push**: the SSE stream polls SQLite every ~0.5s.
- **Single local user, no auth** — local-first by design, not a production
  service.
- **Fail-silent SDK**: if the server is down, events buffer to JSONL and the SDK
  never raises into your agent.
