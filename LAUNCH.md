# LoopLens — Launch Assets

Ready-to-paste launch posts. Attach the demo GIF
(`docs/media/looplens-live-loop-detection.gif`) where noted.

- Repo: <https://github.com/ashutosh-rath02/looplens>
- Docs: <https://ashutosh-rath02.github.io/looplens/>
- PyPI: <https://pypi.org/project/looplens/>

---

## One-liner

> LoopLens — Chrome DevTools for AI agent loops. See your agent run live and get
> warned the moment it repeats itself, burns tokens, retries blindly, or stops
> making progress — and click the warning to jump to exactly where it's stuck.

## The hook (problem → product)

Your agent "works." The terminal scrolls. It looks busy. Then it burns 5 LLM
calls searching the same thing 5 times and gives up — and you only find out from
the final error. LoopLens makes the loop visible *while it runs*, tells you in
plain language that the agent is stuck, and points you to the exact event to fix.

---

## GitHub release notes (v0.7.x)

**LoopLens — a local-first, real-time debugger for AI agent loops.**

- 🔌 **Works with any framework, plug-and-play.** Point any OpenTelemetry
  exporter at the built-in `/v1/traces` receiver (OpenInference / OpenLLMetry) —
  LangChain, LlamaIndex, AutoGen, and more, with **no LoopLens code in your
  agent**. Plus native one-line adapters for **LangGraph**, the **OpenAI Agents
  SDK**, and **CrewAI** (which capture handoffs/guardrails natively).
- 🚨 **Ten transparent loop detectors** — repeated tool call (+ similar-input and
  byte-identical-input variants), no-progress loop, empty-result loop, retry
  storm, long-running step, cost spike, opt-in cost-budget alert, and
  handoff-bounce (agents ping-ponging). Rule-based, no black box.
- 🩺 **Health score + plain-language diagnosis.** Each run gets a 0–100 score
  (Healthy / Warning / Likely stuck / Failed) and a one-line verdict like
  *"Likely stuck — 'search' repeated 5× with no progress."*
- 🎯 **Where do I fix it?** Click a warning to jump straight to the culprit event;
  spot stuck runs at a glance from the runs list; diff two runs side-by-side to
  check a fix.
- 🧩 **Zero-dependency SDK** for the manual path: pure-stdlib `trace()` /
  `event()` / `@observe`, fail-silent (buffers to JSONL if the dashboard's down).
- 🪄 **Zero-friction install:** `pip install "looplens[server]"` — no Node, no
  build step; the dashboard is bundled in the wheel. Local-first: SQLite, no
  auth, no cloud, no API key.

```bash
pip install "looplens[server]"
looplens dev      # dashboard, opens in your browser
looplens demo     # watch it trip a loop warning live
```

MIT.

---

## Hacker News (Show HN)

**Title:** Show HN: LoopLens – a local-first loop debugger for AI agents

**Body:**

I kept shipping agents that *looked* like they were working — logs scrolling,
tools firing — but they were quietly stuck calling the same tool over and over,
burning tokens, and failing at the end. Generic tracing tools show me spans;
they don't tell me the loop is unhealthy or where to fix it.

LoopLens is a small local tool focused on exactly that. It catches the loop while
it runs and raises rule-based warnings — repeated tool call, no-progress loop,
empty-result loop, retry storm, handoff bounce, cost spike — each with a
plain-English "what happened / why / where / how to fix." Click a warning and it
jumps you to the exact offending event.

Getting your agent in is meant to be plug-and-play. There's a universal
OpenTelemetry receiver (so anything with an OpenInference/OpenLLMetry
instrumentor — LangChain, LlamaIndex, AutoGen, … — streams in with zero LoopLens
code), native one-line adapters for LangGraph / OpenAI Agents SDK / CrewAI that
capture handoffs and guardrails, and a zero-dependency SDK for hand-rolled loops.

It's deliberately *not* another observability platform: no auth, no cloud, no
eval datasets, no graph-first UI. Just "is this loop healthy, and where do I fix
it?" — local-first (SQLite), and the `[server]` install ships the prebuilt UI so
there's no Node step.

```bash
pip install "looplens[server]" && looplens dev && looplens demo
```

Repo: https://github.com/ashutosh-rath02/looplens
Docs: https://ashutosh-rath02.github.io/looplens/

Would love feedback — especially on the detectors (false positives/negatives you
hit) and which framework's loops are hardest to see today.

---

## X / Twitter (thread)

1/ Your agent isn't "thinking." It's calling `search_docs("refund policy")` for
the 5th time and about to give up. You find out from the final error.

I built **LoopLens** to make that visible *while it runs* — and to point at the
exact line to fix. 🧵

2/ It's Chrome DevTools, but for agent loops. Watch every LLM call / tool call /
retry / handoff stream in live, with a one-line verdict:
*"Likely stuck — 'search' repeated 5× with no progress."*

3/ The point isn't logs — it's *opinions you can act on*. 10 transparent
detectors: repeated/identical tool calls, no-progress, empty-result loops, retry
storms, handoff bounce, cost spikes. Click a warning → it jumps to the culprit
event.

4/ Plug-and-play with whatever you run:
• any OpenTelemetry agent (LangChain, LlamaIndex, AutoGen…) → zero LoopLens code
• native adapters for LangGraph / OpenAI Agents SDK / CrewAI (handoffs + guardrails)
• a zero-dep SDK for custom loops

5/ Local-first: SQLite, no auth, no cloud, no API key. One-line install, dashboard
ships prebuilt (no Node):
`pip install "looplens[server]" && looplens dev && looplens demo`
[attach GIF]
Repo 👇 https://github.com/ashutosh-rath02/looplens

---

## LinkedIn

Agent development is becoming **loop engineering**. Agents don't answer once —
they plan, call tools, retry, hand off, and loop until success or budget runs
out. When that loop goes wrong it's mostly invisible: the logs look busy while
the agent repeats itself and burns tokens.

I built **LoopLens** — a local-first, real-time debugger focused purely on loop
health. It catches the loop live and raises transparent, rule-based warnings
(repeated tool call, no-progress loop, empty-result loop, retry storm, handoff
bounce, cost spike), each with a plain-English explanation, a one-line diagnosis,
and a click-through to the exact event to fix.

Getting your agent in is plug-and-play: a universal OpenTelemetry receiver covers
any instrumented framework with no LoopLens code, plus native adapters for
LangGraph, the OpenAI Agents SDK, and CrewAI. It's intentionally narrow — not
another observability platform; just the fastest way to see *why your agent got
stuck and where.*

```
pip install "looplens[server]"
looplens dev
looplens demo
```

Open-source (MIT). https://github.com/ashutosh-rath02/looplens

---

## Reddit (r/LocalLLaMA, r/LLMDevs, r/AI_Agents)

**Title:** I built a local-first "loop debugger" for AI agents — see why it got
stuck, and jump to the exact event, live

Sharing a tool I built to scratch my own itch. My agents kept looking busy while
secretly repeating the same tool call and failing at the end. LoopLens shows the
loop live, gives a one-line verdict ("Likely stuck — 'search' repeated 5× with no
progress"), and lets you click the warning to jump to the offending event.

- 10 transparent loop detectors (repeated/identical calls, no-progress,
  empty-result, retry storm, handoff bounce, cost spike, …)
- plug-and-play capture: universal OpenTelemetry receiver (any OpenInference/
  OpenLLMetry-instrumented framework, zero LoopLens code) + native LangGraph /
  OpenAI Agents SDK / CrewAI adapters + a zero-dep SDK for custom loops
- local-first: SQLite, no auth, no cloud, no API key; dashboard bundled (no Node)
- run comparison (before/after a prompt or retry-rule change)

```bash
pip install "looplens[server]" && looplens dev && looplens demo
```

Deliberately narrow (loop health, not full observability).
Repo + docs: https://github.com/ashutosh-rath02/looplens — feedback on the
detectors very welcome.

---

## Demo script (for the GIF / video — ~30s)

1. Split screen: terminal (left) running `looplens demo`, dashboard (right).
2. Watch the timeline fill: `agent_started` → `llm_call` → `tool_call` repeating.
3. By the 3rd `web_search`, the health banner flips to **"Likely stuck — 'web_search'
   repeated …"** and a warning card appears.
4. Health score ticks 100 → "Likely stuck"; the run shows red on the runs list.
5. Click the warning → it jumps to the culprit event; the drawer shows identical
   inputs each call.
6. End card: `pip install "looplens[server]"` + https://github.com/ashutosh-rath02/looplens
