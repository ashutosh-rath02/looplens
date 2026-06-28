# LoopLens — Launch Guide

Everything to take LoopLens public: a step-by-step plan, ready-to-paste posts for
each channel, and prepared answers for the comments you'll get.

- **Repo:** <https://github.com/ashutosh-rath02/looplens>
- **Docs:** <https://ashutosh-rath02.github.io/looplens/>
- **PyPI:** <https://pypi.org/project/looplens/>
- Demo GIF: `docs/media/looplens-live-loop-detection.gif`

---

## 0. Pre-flight checklist (~10 min, do these first)

- [ ] **GitHub repo "About"** (repo home → ⚙️ next to About). Paste:
  - **Description:** `Chrome DevTools for AI agent loops — a local-first, real-time debugger that catches when your agent repeats itself, burns tokens, or stops making progress.`
  - **Website:** `https://ashutosh-rath02.github.io/looplens/`
  - **Topics:** `ai-agents` `llm` `agents` `observability` `debugging` `langgraph` `crewai` `openai-agents` `opentelemetry` `python` `loop-detection`
- [ ] **PyPI page in sync** (published `0.7.2` so the page shows the current README).
- [ ] **Docs live:** <https://ashutosh-rath02.github.io/looplens/> loads.
- [ ] **Local demo dry-run** (so you can screen-share if asked):
  ```bash
  pip install "looplens[server]" && looplens dev   # then: looplens demo
  ```
- [ ] Skim the FAQ in §3 so the "how is this different?" answer is at your fingertips.

## 1. Launch sequence (order + timing)

Lead with Show HN, then fan out. Best window: **Tue–Thu, ~8–10am US Pacific.**

1. **Show HN** — the big one. Immediately add your *first comment* (the backstory).
2. **~30–60 min later: Reddit** — r/LLMDevs and r/LocalLLaMA (use the Reddit copy,
   not the HN text; don't post identical text to both subs).
3. **X / Twitter thread** — post it, pin it, then reply with the HN link once it's up.
4. **LinkedIn** — last.

Then spend the **first 2–3 hours replying to every comment** (HN/Reddit reward
fast, humble, technical engagement — see §4).

---

## 2. The posts (ready to paste)

### 2a. Hacker News — Show HN

**Title:**

```
Show HN: LoopLens – a local-first loop debugger for AI agents
```

**Body:**

```
I kept shipping agents that *looked* like they were working — logs scrolling,
tools firing — but they were quietly stuck calling the same tool over and over,
burning tokens, and failing at the end. Generic tracing tools show me spans;
they don't tell me the loop is unhealthy or where to fix it.

LoopLens is a small local tool focused on exactly that. It catches the loop while
it runs and raises rule-based warnings — repeated tool call, no-progress loop,
empty-result loop, retry storm, handoff bounce, cost spike — each with a
plain-English "what happened / why / where / how to fix." Click a warning and it
jumps you to the exact offending event.

Getting your agent in is meant to be plug-and-play: a universal OpenTelemetry
receiver (so anything with an OpenInference/OpenLLMetry instrumentor — LangChain,
LlamaIndex, AutoGen, … — streams in with zero LoopLens code), native one-line
adapters for LangGraph / OpenAI Agents SDK / CrewAI that capture handoffs and
guardrails, and a zero-dependency SDK for hand-rolled loops.

It's deliberately *not* another observability platform: no auth, no cloud, no
eval datasets, no graph-first UI. Just "is this loop healthy, and where do I fix
it?" — local-first (SQLite), and the [server] install ships the prebuilt UI so
there's no Node step.

  pip install "looplens[server]" && looplens dev && looplens demo

Repo: https://github.com/ashutosh-rath02/looplens
Docs: https://ashutosh-rath02.github.io/looplens/

Would love feedback — especially on the detectors (false positives/negatives you
hit) and which framework's loops are hardest to see today.
```

**Your first comment** (post immediately after submitting):

```
A bit more on the "why": every agent framework gives you a trace viewer now, but
a trace is just spans — you still have to eyeball it and decide the agent is
stuck. I wanted the tool to have an opinion: "Likely stuck — 'search' repeated 5×
with no progress," and one click to the culprit event.

The detectors are all transparent rules (no scoring black box) so you can see
exactly why a warning fired, and the base SDK is pure stdlib so it won't fight
your agent's deps. Happy to go deep on any of the detection rules.
```

### 2b. Reddit (r/LLMDevs, r/LocalLLaMA, r/AI_Agents)

**Title:**

```
I built a local-first "loop debugger" for AI agents — see why it got stuck, and jump to the exact event, live
```

**Body:**

```
Sharing a tool I built to scratch my own itch. My agents kept looking busy while
secretly repeating the same tool call and failing at the end. LoopLens shows the
loop live, gives a one-line verdict ("Likely stuck — 'search' repeated 5× with no
progress"), and lets you click the warning to jump to the offending event.

- 10 transparent loop detectors (repeated/identical calls, no-progress,
  empty-result, retry storm, handoff bounce, cost spike, …)
- plug-and-play capture: a universal OpenTelemetry receiver (any OpenInference/
  OpenLLMetry-instrumented framework, zero LoopLens code) + native LangGraph /
  OpenAI Agents SDK / CrewAI adapters + a zero-dep SDK for custom loops
- local-first: SQLite, no auth, no cloud, no API key; dashboard bundled (no Node)
- run comparison (before/after a prompt or retry-rule change)

    pip install "looplens[server]" && looplens dev && looplens demo

Deliberately narrow (loop health, not full observability).
Repo + docs: https://github.com/ashutosh-rath02/looplens

Feedback on the detectors very welcome — what loops have burned you?
```

### 2c. X / Twitter (thread)

```
1/ Your agent isn't "thinking." It's calling search_docs("refund policy") for the
5th time and about to give up. You find out from the final error.

I built LoopLens to make that visible *while it runs* — and point at the exact
line to fix. 🧵

2/ It's Chrome DevTools, but for agent loops. Watch every LLM call / tool call /
retry / handoff stream in live, with a one-line verdict:
"Likely stuck — 'search' repeated 5× with no progress."

3/ The point isn't logs — it's opinions you can act on. 10 transparent detectors:
repeated/identical tool calls, no-progress, empty-result loops, retry storms,
handoff bounce, cost spikes. Click a warning → jump to the culprit event.

4/ Plug-and-play with whatever you run:
• any OpenTelemetry agent (LangChain, LlamaIndex, AutoGen…) → zero LoopLens code
• native adapters for LangGraph / OpenAI Agents SDK / CrewAI (handoffs + guardrails)
• a zero-dep SDK for custom loops

5/ Local-first: SQLite, no auth, no cloud, no API key. One line, dashboard ships
prebuilt (no Node):
pip install "looplens[server]" && looplens dev && looplens demo
[attach the GIF]
Repo 👇 https://github.com/ashutosh-rath02/looplens
```

### 2d. LinkedIn

```
Agent development is becoming loop engineering. Agents don't answer once — they
plan, call tools, retry, hand off, and loop until success or budget runs out.
When that loop goes wrong it's mostly invisible: the logs look busy while the
agent repeats itself and burns tokens.

I built LoopLens — a local-first, real-time debugger focused purely on loop
health. It catches the loop live and raises transparent, rule-based warnings
(repeated tool call, no-progress loop, empty-result loop, retry storm, handoff
bounce, cost spike), each with a plain-English explanation, a one-line diagnosis,
and a click-through to the exact event to fix.

Getting your agent in is plug-and-play: a universal OpenTelemetry receiver covers
any instrumented framework with no LoopLens code, plus native adapters for
LangGraph, the OpenAI Agents SDK, and CrewAI. It's intentionally narrow — not
another observability platform; just the fastest way to see why your agent got
stuck and where.

  pip install "looplens[server]"
  looplens dev
  looplens demo

Open-source (MIT). https://github.com/ashutosh-rath02/looplens
```

---

## 3. FAQ — answers to keep ready for comments

**"How is this different from LangSmith / Langfuse / Phoenix / Helicone?"**
> Those are great observability platforms — they show you traces/spans and you
> interpret them. LoopLens is a loop debugger: it gives an opinion ("Likely stuck
> — 'search' repeated 5× with no progress") and clicks you to the exact event to
> fix. It's local-first (SQLite, no account/key), the detection is transparent
> rules (no black box), and it deliberately isn't a full APM. Use it alongside
> your tracer, not instead of it.

**"Does it need an API key / send my data anywhere?"**
> No key, no account, no cloud. Events go to `127.0.0.1` only; SQLite on disk. The
> SDK is a no-op when `LOOPLENS_ENABLED=false`.

**"Does it work with <my framework>?"**
> If it emits OpenTelemetry (OpenInference/OpenLLMetry) it works with zero LoopLens
> code via `/v1/traces`. There are native adapters for LangGraph, the OpenAI
> Agents SDK, and CrewAI, and a zero-dep SDK for anything hand-rolled.

**"Rule-based detection — won't it false-positive?"**
> The rules are conservative and transparent (you can read every one). E.g.
> empty-result only counts completed calls that actually returned a result, and a
> handoff bounce needs a genuine two-agent ping-pong. Feedback on edge cases is
> exactly what I'm looking for.

**"Why not just use my framework's built-in tracing?"**
> You can — point its OTel exporter at LoopLens. The difference is the verdict and
> the loop-specific detectors, not another span viewer.

---

## 4. During the launch (first few hours)

- **Reply to every comment**, fast. Be humble and technical; never defensive.
- Thank critics; turn feature requests into GitHub issues live ("good idea —
  opened #N").
- If a bug surfaces: reproduce, acknowledge, and ship a `0.7.x` patch quickly —
  shipping during the thread is a great signal.
- Pin the best comment/clarification to the top.

## 5. After

- Open GitHub issues for the recurring requests; reply on the thread linking them.
- A short "thanks + what I learned + what's next" follow-up a day later does well.
- Roadmap candidates that fit the wedge: more detectors, AutoGen/Pydantic AI
  adapters (only if asked for), a graph view (kept after the timeline).
