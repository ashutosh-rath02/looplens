# LoopLens — Launch Assets

Copy-paste launch posts for each channel. Replace `REPO_URL` with the GitHub
link and attach the demo GIF where noted.

---

## One-liner

> LoopLens — Chrome DevTools for AI agent loops. See your agent run live and get
> warned the moment it repeats itself, retries blindly, or stops making progress.

## The hook (problem → product)

Your agent "works." The terminal scrolls. It looks busy. Then it burns 5 LLM
calls searching the same thing 5 times and gives up — and you only find out from
the final error. LoopLens makes the loop visible *while it runs* and tells you,
in plain language, that the agent is stuck and where.

---

## GitHub release notes (v0.1.0)

**LoopLens v0.1.0 — local-first loop debugger for AI agents.**

- 🪄 **Zero-friction install:** `pip install "looplens[server]"` — no Node, no
  build step; the dashboard is bundled in the wheel.
- 🧩 **Zero-dependency SDK:** pure-stdlib `trace()` / `event()` / `@observe`.
  Drops into LangGraph, CrewAI, OpenAI Agents SDK, or a plain `while` loop
  without pinning anything or touching your agent's deps.
- 📺 **Live timeline** over SSE: LLM calls, tool calls, retries, handoffs, state.
- 🚨 **Six transparent loop detectors:** repeated tool call, similar-input
  repeat, no-progress loop, retry storm, long-running step, cost spike.
- 🩺 **Health score** (0–100 → Healthy / Warning / Likely stuck / Failed).
- 💾 **Local-first:** SQLite, no auth, no cloud, no API key. JSONL import/export.
- 🛟 **Fail-silent:** if the dashboard is down, the SDK buffers to JSONL and
  never crashes your agent.

```bash
pip install "looplens[server]"
looplens dev
looplens demo   # watch it trip a loop warning live
```

MIT. Feedback and framework-adapter requests welcome.

---

## Hacker News (Show HN)

**Title:** Show HN: LoopLens – a local-first loop debugger for AI agents

**Body:**

I kept shipping agents that *looked* like they were working — the logs scrolled,
tools fired — but they were quietly stuck calling the same tool over and over,
burning tokens, and failing at the end. Generic tracing tools show me spans;
they don't tell me the loop is unhealthy.

LoopLens is a small local tool focused on exactly that. You add a tiny zero-dep
SDK to the agent you already have, run a local dashboard, and watch the loop live.
It raises rule-based warnings — repeated tool call, no-progress loop, retry
storm, cost spike — with a plain-English "what happened / why it matters / where /
how to fix."

It's deliberately *not* another observability platform: no auth, no cloud, no
eval datasets, no graph-first UI. Just timeline + warnings + metrics, local-first.

The detectors are transparent rules (no black-box scoring), the SDK is pure
stdlib so it won't fight your agent's dependencies, and the `[server]` install
ships the prebuilt UI so there's no Node/npm step.

```bash
pip install "looplens[server]" && looplens dev && looplens demo
```

Repo: REPO_URL — would love feedback, especially on which framework adapter
(LangGraph / CrewAI / OpenAI Agents SDK) to build first.

---

## X / Twitter (thread)

1/ Your agent isn't "thinking." It's calling `search_docs("refund policy")` for
the 5th time and about to give up. You'll find out from the final error.

I built **LoopLens** to make that visible *while it runs.* 🧵

2/ It's Chrome DevTools, but for agent loops. Add a tiny zero-dep SDK, open a
local dashboard, watch every LLM call / tool call / retry stream in live.

3/ The point isn't logs — it's *opinions*. LoopLens warns you:
• repeated tool call
• no-progress loop
• retry storm
• cost spike
…each with what happened, why, where, and how to fix.

4/ Local-first: SQLite, no auth, no cloud, no API key. The SDK is pure stdlib so
it won't conflict with LangGraph / CrewAI / OpenAI Agents SDK / your custom loop.
If the dashboard's down it buffers to JSONL and never crashes your agent.

5/ Install is one line — the dashboard ships prebuilt, no Node:
`pip install "looplens[server]" && looplens dev && looplens demo`
[attach GIF]
Repo + roadmap 👇 REPO_URL

---

## LinkedIn

Agent development is becoming **loop engineering**. Agents don't answer once —
they plan, call tools, retry, hand off, and loop until success or budget runs
out. When that loop goes wrong, it's mostly invisible: the logs look busy while
the agent repeats itself and burns tokens.

I built **LoopLens** — a local-first, real-time debugger focused purely on loop
health. Add a zero-dependency Python SDK to the agent you already have, open a
local dashboard, and watch the run live. It raises transparent, rule-based
warnings — repeated tool call, no-progress loop, retry storm, cost spike — each
with a plain-English explanation and a suggested fix.

It's intentionally narrow: not another observability platform — no auth, no
cloud, no eval suite. Just the fastest way to see *why your agent got stuck.*

```
pip install "looplens[server]"
looplens dev
looplens demo
```

Open-source (MIT). Roadmap includes LangGraph / CrewAI / OpenAI Agents SDK
adapters — feedback on ordering welcome. REPO_URL

---

## Reddit (r/LangChain, r/AI_Agents, r/LocalLLaMA)

**Title:** I built a local-first "loop debugger" for AI agents — see why it got
stuck, live

Sharing a tool I built to scratch my own itch. My agents kept looking busy while
secretly repeating the same tool call and failing at the end. LoopLens shows the
loop live and warns you the moment it detects repeated calls, no-progress loops,
retry storms, or cost spikes — in plain language, with a suggested fix.

- zero-dependency SDK (pure stdlib — drops into LangGraph/CrewAI/OpenAI Agents
  SDK/custom loops without dependency conflicts)
- local-first: SQLite, no auth, no cloud, no API key
- one-line install, dashboard bundled (no Node build step)
- fail-silent: buffers to JSONL if the dashboard's down, never crashes your agent

```bash
pip install "looplens[server]" && looplens dev && looplens demo
```

It's an MVP and deliberately narrow (loop health, not full observability).
Repo + roadmap: REPO_URL. What framework adapter should I build first?

---

## Demo script (for the GIF / video — ~30s)

1. Split screen: terminal (left) running `looplens demo`, dashboard (right).
2. Watch the timeline fill: `agent_started` → `llm_call` → `tool_call` repeating.
3. By the 3rd `web_search`, a **warning card** appears: *"Same tool called
   repeatedly with similar input — possible no-progress loop."*
4. Health score ticks down from 100 → "Likely stuck."
5. Click an event → drawer shows the raw JSON (identical inputs each call).
6. End card: `pip install "looplens[server]"` + repo URL.
