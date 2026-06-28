# Roadmap

The MVP is feature-complete: a zero-dep SDK, a FastAPI + SQLite backend, a CLI, a
React dashboard, live SSE streaming, ten rule-based [loop detectors](detectors.md),
universal [OpenTelemetry ingestion](opentelemetry.md), and a
[LangGraph adapter](langgraph.md).

The full, always-current plan lives in
[`ROADMAP.md`](https://github.com/ashutosh-rath02/looplens/blob/main/ROADMAP.md).
The highlights:

## Recently shipped

- **Universal OpenTelemetry ingestion** at `POST /v1/traces` — any
  OpenInference / OpenLLMetry instrumented framework, no LoopLens code.
- **LangGraph / LangChain adapter** for tight in-process capture.
- **OpenAI Agents SDK adapter** — a native `TracingProcessor` that captures
  handoffs and guardrails, not just LLM/tool calls.
- **CrewAI adapter** — a `BaseEventListener` that captures crew delegation as
  handoffs, so a stuck crew trips `handoff_bounce`.
- **Handoff capture** — `transfer_to_<agent>` tool calls become
  `handoff_started` events, so `handoff_bounce` fires through both paths.
- Three more detectors — **exact tool+args repeat**, **empty-result loop**, and
  opt-in **cost-budget alerts** (`LOOPLENS_COST_BUDGET`).
- **Run comparison** — a `/compare` view that diffs two runs side by side
  (health, metrics with coloured deltas, and each run's loop warnings).
- **PyPI release** with a UI-bundled wheel, CI matrix (3.10–3.13), `looplens
  doctor`, and browser auto-open.

## Next

1. **AutoGen** and **Pydantic AI** adapters.
2. **Simple graph view** — an agent/tool transition graph, after the timeline.
3. **Arbitrary node-to-node handoffs** — beyond the transfer-tool convention,
   without flagging healthy loops.

## Later

A graph view, semantic similarity via embeddings, replay-from-step, and an
opt-in LLM-based diagnosis layered on top of the transparent rules.

## Out of scope

LoopLens stays a **loop debugger**, not a general observability platform. No
prompt-versioning suite, no eval-dataset product, no full OTel backend, no
graph-first UI in the core.
