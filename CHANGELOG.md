# Changelog

All notable changes to LoopLens are documented here. This project follows
[Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- **CrewAI adapter** (`looplens.integrations.crewai`) — a `BaseEventListener`
  that maps crew bus events to LoopLens events and emits `handoff_started` when
  control moves to a different agent, so a stuck crew trips `handoff_bounce`.
  Install with `pip install "looplens[crewai]"`.

## 0.4.0

### Added

- **OpenAI Agents SDK adapter** (`looplens.integrations.openai_agents`) — a
  native `TracingProcessor` that maps the SDK's generation, tool, **handoff**,
  and **guardrail** spans to LoopLens events. `instrument()` is a one-liner.
  Install with `pip install "looplens[openai-agents]"`.

## 0.3.0

### Added

- **Run comparison** (`/compare`) — diff two runs side by side: health badges, a
  metrics table with colour-coded deltas (green when a metric moves the better
  way), and which loop warnings each run raised. The before/after view for a
  prompt or retry-rule change.

### Changed

- The dashboard now uses the **full viewport width** instead of a centered
  ~1152px column.

## 0.2.0

The "works with any framework" release. Capture is no longer manual-only, and the
detector set is twice as deep.

### Added

- **Universal OpenTelemetry ingestion** (`POST /v1/traces`). Any framework that
  emits OpenInference / OpenLLMetry / `gen_ai.*` spans — LangChain/LangGraph,
  LlamaIndex, CrewAI, AutoGen, the OpenAI Agents SDK, … — streams in with no
  LoopLens code in the agent. OTLP/JSON works out of the box; OTLP/protobuf via
  `pip install "looplens[otel]"`.
- **LangGraph / LangChain adapter** (`looplens.integrations.langgraph`) — a
  callback handler that captures every node's LLM and tool calls. Install with
  `pip install "looplens[langgraph]"`.
- **Handoff capture** — `transfer_to_<agent>` / `handoff_to_<agent>` tool calls
  become `handoff_started` events, so `handoff_bounce` fires through both the OTel
  and LangGraph paths.
- New detectors: `repeated_tool_call_exact_input` (byte-identical repeats),
  `empty_result_loop` (a tool returning "no results" repeatedly), and the opt-in
  `cost_budget_exceeded` (`LOOPLENS_COST_BUDGET`).
- `looplens doctor` — checks the port, the SDK→server round-trip, and the JSONL
  fallback.
- `looplens dev` opens the dashboard in your browser automatically (`--no-open`).
- A documentation site (MkDocs Material) and a CHANGELOG.

### Changed

- `repeated_tool_call` now slides its window over **tool calls**, not raw events,
  so interleaved ReAct traces trip it.
- The published wheel bundles the prebuilt UI (the sdist now carries it too, so
  the wheel built from the sdist keeps it).

### Infrastructure

- GitHub Actions CI (Python 3.10–3.13 + a UI build check) and a trusted-publishing
  release workflow that verifies the tag matches the package version and that the
  UI is bundled in the wheel.

## 0.1.0

Initial release: zero-dependency SDK (`trace` / `event` / `@observe`), FastAPI +
SQLite backend, Typer CLI, React dashboard with live SSE streaming, six
rule-based loop detectors, and JSONL import/export.
