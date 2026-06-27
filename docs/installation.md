# Installation

LoopLens ships as two layers: a zero-dependency **SDK** you add to your agent,
and an optional **dashboard** (`[server]`) you open when you want to look.

```bash
pip install looplens             # the SDK (drop into your agent — zero deps)
pip install "looplens[server]"   # adds the dashboard (FastAPI + prebuilt UI)
```

That's it — **no Node, no npm, no build step.** The `[server]` extra ships the
compiled React dashboard inside the wheel, so `looplens dev` serves a ready UI on
the first run.

`pipx install "looplens[server]"`, `uv pip install`, and `uv tool install` work
the same way.

## Optional extras

| Extra | Install | Adds |
| --- | --- | --- |
| `server` | `pip install "looplens[server]"` | the dashboard (FastAPI + bundled UI) |
| `otel` | `pip install "looplens[otel]"` | OTLP/protobuf decoding for [OpenTelemetry ingestion](opentelemetry.md) |
| `langgraph` | `pip install "looplens[langgraph]"` | the [LangGraph / LangChain adapter](langgraph.md) |

## Why it installs cleanly anywhere

The base `looplens` SDK is **pure Python stdlib with zero third-party
dependencies**, so it pins nothing and sits next to any agent stack —
**LangGraph / LangChain**, **CrewAI**, **AutoGen**, **OpenAI Agents SDK**,
**Pydantic AI**, or a hand-rolled `while` loop.

- No API key, no login, no network egress — events go to `127.0.0.1` only, and
  the SDK is a no-op when `LOOPLENS_ENABLED=false`.
- Fail-silent by design: if the dashboard isn't running it buffers to JSONL and
  **never raises into your agent**.

## Verify the install

```bash
looplens doctor   # checks the port, the SDK -> server round-trip, and JSONL fallback
```

See the [CLI reference](cli.md) for all commands.
