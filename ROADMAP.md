# LoopLens Roadmap

The MVP is feature-complete (PRD §26): zero-dep SDK, FastAPI + SQLite backend,
CLI, React dashboard, live SSE streaming, ten rule-based loop detectors, and a
demo that reliably trips a warning. This roadmap is what comes next, ordered by
value-to-effort.

**Recently shipped** (validated against real GitHub loop patterns —
[langgraph#6731](https://github.com/langchain-ai/langgraph/issues/6731),
[langchain#36139](https://github.com/langchain-ai/langchain/issues/36139)):
the `repeated_tool_call` window now slides over *tool calls* instead of raw
events (so interleaved ReAct traces trip it — confirmed on a live OpenAI run),
and the **handoff-bounce** detector (PRD §17 Rule 7) catches A→B→A→B agent
oscillation.

Also shipped: **CI** (`.github/workflows/ci.yml`) — a Python 3.10–3.13 matrix
running `pytest` plus a UI build check — and a **release workflow**
(`.github/workflows/release.yml`) that builds the UI, builds the wheel (UI
force-bundled), verifies the bundle is inside the wheel, and publishes to PyPI
on a `v*` tag via trusted publishing. Plus **`looplens doctor`** (checks the
port, the SDK→server round-trip, and the JSONL fallback) and **auto-open** of
the dashboard on `looplens dev` (with `--no-open`).

And two more detectors: the **exact tool+args repeat**
(`repeated_tool_call_exact_input`) flags byte-identical `(tool, normalized args)`
repeats as the highest-confidence loop signal short of `no_progress` — the
canonical LangGraph / deer-flow bug, complementing the fuzzy `similar_input`
rule; and the **empty-result loop** (`empty_result_loop`) flags a tool that
returns empty / "no results" ≥3× (only judging completed calls that carry an
output, so a missing output never false-positives).

## Now → next (the immediate backlog)

These are the smallest steps that most increase adoption.

- **Finish the PyPI release.** Workflow is in place; remaining one-time setup:
  register the project on PyPI and configure the `pypi` environment for trusted
  publishing (OIDC), then cut the first tag (`git tag v0.1.0 && git push --tags`).
- **More README screenshots.** The live-loop demo GIF is embedded
  (`docs/media/`); add static stills of the run detail (warning cards) and the
  event drawer for users who don't autoplay GIFs.

## V1 — framework adapters (kill manual instrumentation)

The biggest friction today is hand-placing `event()` calls. V1 makes LoopLens
auto-capture from the frameworks people already use (PRD §21).

**Shipped — universal OpenTelemetry ingestion.** The server exposes an OTLP/HTTP
receiver at `POST /v1/traces`. Any framework that emits OpenInference /
OpenLLMetry / `gen_ai.*` spans — LangChain/LangGraph, LlamaIndex, CrewAI,
AutoGen, the OpenAI Agents SDK, … — streams in by pointing its OTLP exporter at
LoopLens, with no LoopLens code in the agent. OTLP/JSON needs nothing; OTLP
/protobuf needs `pip install "looplens[otel]"`. This is the no-lock-in path that
covers the long tail of frameworks at once.

**Shipped — LangGraph / LangChain adapter.** `LoopLensCallbackHandler` (in
`looplens.integrations.langgraph`) is a LangChain callback handler for a tighter
in-process integration; captures every node's LLM and tool calls (plus run
boundary, tokens, latencies). Install with `pip install "looplens[langgraph]"`.

**Shipped — handoff capture.** Both the OTel mapper and the LangGraph adapter
recognise `transfer_to_<agent>` / `handoff_to_<agent>` tool calls (the LangGraph
supervisor/swarm and CrewAI convention) and emit `handoff_started` events, so
`handoff_bounce` fires on agent oscillation. Matching the transfer-tool
convention — not every node transition — keeps a normal ReAct `agent`↔`tools`
loop from looking like a bounce.

Next, in order:

1. **OpenAI Agents SDK** — consume its tracing hooks (tool calls, handoffs,
   guardrails) directly, for richer signal than the generic OTel spans.
2. **CrewAI** — capture crew handoffs and task timelines (where repetition hides).
3. **AutoGen** and **Pydantic AI** adapters.
4. **Arbitrary node-to-node handoffs** — map graph node transitions (beyond the
   transfer-tool convention) to handoff events without flagging healthy loops.

**Shipped — cost-budget alerts.** Set `LOOPLENS_COST_BUDGET` (USD) and a run whose
total cost crosses it raises a `cost_budget_exceeded` warning — catches a runaway
loop burning spend. Opt-in, so it's a no-op until configured.

**Shipped — run comparison.** A `/compare` view diffs two runs side by side —
health, metrics (with coloured deltas), and which loop warnings each run raised —
for before/after a prompt or retry-rule change.

Also in V1:

- **Simple graph view** — agent/tool transition graph, *after* the timeline.

## V2 — smarter diagnosis

- **Semantic similarity** via embeddings (replace string-similarity for
  repeated-input detection).
- **Replay from step** — re-run an agent from any event.
- **Prompt-change comparison** — quantify loop-depth deltas across prompt edits.
- **LLM-based diagnosis** — an opt-in pass that explains *why* a loop happened
  and suggests a fix, layered on top of the transparent rules (never replacing
  them).
- **Tool-output mutation testing**; **WebSocket push** to replace the 0.5s poll.

## V3 — team & production

- Hosted dashboard, team workspaces, trace sharing.
- Production alerting (Slack), regression testing, **CI loop checks**
  (fail a build when an agent's loop health regresses).
- Eval integration.

## Explicitly *not* doing (keeps the wedge sharp)

LoopLens stays a **loop debugger**, not a general observability platform. No
prompt-versioning suite, no eval-dataset product, no full OTel backend, no
graph-first UI in the core. If a feature doesn't help answer *"is this agent's
loop healthy, and where do I fix it?"*, it's out of scope.
