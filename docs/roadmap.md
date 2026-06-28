# Roadmap

The MVP is feature-complete: a zero-dep SDK, a FastAPI + SQLite backend, a CLI, a
React dashboard, live SSE streaming, nine rule-based [loop detectors](detectors.md),
universal [OpenTelemetry ingestion](opentelemetry.md), and a
[LangGraph adapter](langgraph.md).

The full, always-current plan lives in
[`ROADMAP.md`](https://github.com/ashutosh-rath02/looplens/blob/main/ROADMAP.md).
The highlights:

## Recently shipped

- **Universal OpenTelemetry ingestion** at `POST /v1/traces` — any
  OpenInference / OpenLLMetry instrumented framework, no LoopLens code.
- **LangGraph / LangChain adapter** for tight in-process capture.
- **Exact tool+args repeat detector** — byte-identical repeats as a
  high-confidence loop signal.
- **PyPI release** with a UI-bundled wheel, CI matrix (3.10–3.13), `looplens
  doctor`, and browser auto-open.

## Next

1. **OpenAI Agents SDK** adapter — consume its tracing hooks directly.
2. **CrewAI** adapter — crew handoffs and task timelines.
3. **Agent / node transitions → handoff events** in both the OTel mapper and the
   LangGraph adapter, so `handoff_bounce` fires on graph oscillation.
4. **Empty/ambiguous-result loop** detector — flag a tool that returns
   "no results" repeatedly.

## Later

Run comparison, a graph view, cost-budget alerts, semantic similarity via
embeddings, replay-from-step, and an opt-in LLM-based diagnosis layered on top of
the transparent rules.

## Out of scope

LoopLens stays a **loop debugger**, not a general observability platform. No
prompt-versioning suite, no eval-dataset product, no full OTel backend, no
graph-first UI in the core.
