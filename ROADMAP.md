# LoopLens Roadmap

The MVP is feature-complete (PRD §26): zero-dep SDK, FastAPI + SQLite backend,
CLI, React dashboard, live SSE streaming, eight rule-based loop detectors, and a
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

And the **exact tool+args repeat** detector (`repeated_tool_call_exact_input`):
flags byte-identical `(tool, normalized args)` repeats as the highest-confidence
loop signal short of `no_progress` — the canonical LangGraph / deer-flow bug,
complementing the fuzzy `similar_input` rule.

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

**Shipped:** **LangGraph / LangChain** — `LoopLensCallbackHandler` (in
`looplens.integrations.langgraph`) is a LangChain callback handler, so it
captures every node's LLM and tool calls (plus the run boundary, tokens, and
latencies) with no manual `event()` calls. Install with
`pip install "looplens[langgraph]"`.

Next, in order:

1. **OpenAI Agents SDK** — consume its tracing hooks (tool calls, handoffs,
   guardrails) directly.
2. **CrewAI** — capture crew handoffs and task timelines (where repetition hides).
3. **AutoGen** and **Pydantic AI** adapters.
4. **Generic OpenTelemetry / OpenInference import** — avoid vendor lock-in.
5. **Map LangGraph node transitions → handoff events** so `handoff_bounce` fires
   on graph oscillation (the current adapter captures LLM/tool calls, not yet
   node-to-node handoffs).

Also in V1:

- **Run comparison** — diff two runs (before/after a prompt or retry-rule change).
- **Simple graph view** — agent/tool transition graph, *after* the timeline.
- **Cost-budget alerts** — warn when a run crosses a configured $ ceiling.
- **Empty/ambiguous-result loop** — flag a tool that returns empty / "no results"
  repeatedly (a documented root cause of reasoning loops); needs output
  inspection. The natural follow-on now that the exact-repeat rule has shipped.

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
