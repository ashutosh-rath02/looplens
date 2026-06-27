# LoopLens Roadmap

The MVP is feature-complete (PRD §26): zero-dep SDK, FastAPI + SQLite backend,
CLI, React dashboard, live SSE streaming, six rule-based loop detectors, and a
demo that reliably trips a warning. This roadmap is what comes next, ordered by
value-to-effort.

## Now → next (the immediate backlog)

These are the smallest steps that most increase adoption.

- **Publish to PyPI.** Ship the wheel (UI already bundled — `pip install
  "looplens[server]"` needs no Node). Add a release workflow that runs
  `npm --prefix ui run build` then `python -m build` and uploads on tag.
- **CI.** GitHub Actions matrix (3.10–3.13) running `pytest`, plus a UI build
  check. Gate releases on green.
- **Auto-open the browser** on `looplens dev` (with a `--no-open` flag).
- **Screenshots + demo GIF in the README.** Live timeline filling in, a warning
  card firing, the health score dropping.
- **`looplens doctor`** — one command that checks the port, the SDK→server
  round-trip, and the JSONL fallback path, so onboarding never silently fails.

## V1 — framework adapters (kill manual instrumentation)

The biggest friction today is hand-placing `event()` calls. V1 makes LoopLens
auto-capture from the frameworks people already use, in this order (PRD §21):

1. **LangGraph** — wrap the graph/state loop; map nodes → events natively.
2. **OpenAI Agents SDK** — consume its tracing hooks (tool calls, handoffs,
   guardrails) directly.
3. **CrewAI** — capture crew handoffs and task timelines (where repetition hides).
4. **AutoGen** and **Pydantic AI** adapters.
5. **Generic OpenTelemetry / OpenInference import** — avoid vendor lock-in.

Also in V1:

- **Run comparison** — diff two runs (before/after a prompt or retry-rule change).
- **Simple graph view** — agent/tool transition graph, *after* the timeline.
- **Cost-budget alerts** — warn when a run crosses a configured $ ceiling.
- **Handoff-bounce detector** (PRD §17 Rule 7) — A→B→A→B ping-pong.

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
