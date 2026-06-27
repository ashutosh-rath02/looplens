# PRD: LoopLens — Real-Time Loop Debugger for AI Agents

## 1. Product Name

**LoopLens**

## 2. One-Line Description

LoopLens is a local-first real-time debugger that shows AI agent execution loops live and detects when agents repeat themselves, burn tokens, retry blindly, or stop making progress.

## 3. Product Positioning

### Primary positioning

**Chrome DevTools for AI agent loops.**

### Secondary positioning

**See why your agent got stuck.**

### Practical positioning

LoopLens is not another generic LLM observability platform. It is a focused developer tool for inspecting, diagnosing, and improving loop behavior in AI agents.

It helps developers answer:

* Is my agent making progress?
* Why is it repeating the same tool call?
* Which step caused the loop?
* Which agent is wasting cost?
* Did the retry actually help?
* Did handoff improve the result or make it worse?
* Did my prompt change reduce or increase loop depth?
* Where should I add a guardrail, max-step limit, or state update?

---

# 4. Market Context

AI agent development is moving from one-shot prompting to loop-based systems.

Modern agents do not simply answer once. They repeatedly:

1. receive a goal
2. plan
3. call an LLM
4. call tools
5. update state
6. read/write memory
7. retry on failure
8. hand off to another agent
9. continue until success, failure, budget limit, or human intervention

This creates a new debugging problem.

Traditional software debugging shows deterministic code paths. LLM agent debugging needs visibility into non-deterministic trajectories.

Existing platforms provide tracing and observability, but they are usually broad platforms. They show what happened, but they often do not deeply explain whether the loop itself is healthy.

LoopLens focuses specifically on loop behavior.

---

# 5. Problem Statement

Developers building agents today struggle with invisible loop failure.

Common problems:

## 5.1 Repeated tool calls

The agent keeps calling the same tool with the same or similar input.

Example:

```txt
search_docs("refund policy")
search_docs("refund policy")
search_docs("refund policy")
```

The developer sees the final failure, but not the exact repeated pattern.

## 5.2 No-progress loops

The agent takes many steps but does not change state meaningfully.

Example:

```txt
plan -> search -> observe -> plan -> search -> observe
```

The trace is long, but the useful state remains unchanged.

## 5.3 Retry storms

The agent keeps retrying failed calls without changing strategy.

Example:

```txt
tool_failed
retry
tool_failed
retry
tool_failed
retry
```

## 5.4 Cost blowups

One loop iteration may look small, but repeated LLM calls, tool calls, and sub-agent calls can silently increase cost.

## 5.5 Bad handoffs

Agent A hands off to Agent B, but Agent B repeats the same work or loses context.

## 5.6 Hard-to-read traces

Generic traces show spans, logs, and metadata, but developers still need to manually inspect whether the agent behaved intelligently.

LoopLens should convert raw trace activity into loop-level diagnosis.

---

# 6. Target Users

## 6.1 Primary user

AI engineers building agents with:

* LangGraph
* LangChain
* OpenAI Agents SDK
* CrewAI
* AutoGen
* Pydantic AI
* custom Python agent loops
* Claude Code / Codex-style coding agent workflows

## 6.2 Secondary user

* LLM application developers
* agent framework builders
* AI infra engineers
* evaluation engineers
* developer-tooling teams
* researchers studying agent behavior

## 6.3 Initial ideal customer profile

A solo developer or small AI team building agentic workflows locally and wanting to debug agent execution before production.

---

# 7. User Personas

## Persona 1: Agent Builder

“I built a LangGraph agent, but it keeps looping. I need to see where and why.”

Needs:

* live trace
* state changes
* tool-call sequence
* repeated action detection
* step replay later

## Persona 2: AI Full-Stack Developer

“I am building an agent app and need a quick debugging UI without setting up a full SaaS observability stack.”

Needs:

* local-first setup
* simple SDK
* CLI
* UI
* JSONL export

## Persona 3: Coding Agent Power User

“I run Claude Code/Codex-style workflows and want to know where loops waste time and tokens.”

Needs:

* CLI trace import
* cost estimate
* repeated command/tool detection
* run comparison

## Persona 4: Agent Framework Maintainer

“I want a simple way to visualize loop health in my framework.”

Needs:

* clean schema
* adapter API
* OTel-compatible future
* embeddable viewer

---

# 8. Competitive Landscape

## 8.1 LangSmith

Strengths:

* mature tracing
* LangChain/LangGraph integration
* run trees
* cost tracking
* prompt iteration
* Studio for graph debugging and replay

Weakness for our use case:

* broader platform
* strongest inside LangChain/LangGraph ecosystem
* loop-health diagnosis is not the primary product identity

## 8.2 Langfuse

Strengths:

* open-source
* tracing
* prompt/version management
* evals
* cost tracking
* many framework integrations

Weakness for our use case:

* broad LLM observability platform
* loop-specific UX is not the core focus

## 8.3 Arize Phoenix

Strengths:

* open-source
* OpenTelemetry/OpenInference orientation
* tracing
* evals
* datasets
* experiments
* replay

Weakness for our use case:

* more observability/evaluation focused
* not positioned as a fast loop debugger

## 8.4 OpenAI Agents SDK Traces

Strengths:

* native tracing for OpenAI Agents SDK
* captures LLM generations, tool calls, handoffs, guardrails, custom events
* useful dashboard

Weakness for our use case:

* framework/provider-specific
* not an independent loop-diagnosis layer

## 8.5 CrewAI AMP / AgentOps

Strengths:

* agent and crew monitoring
* tool usage
* task timeline
* cost
* production monitoring

Weakness for our use case:

* tied to platform/workflow ecosystem
* broad operations focus

## 8.6 Helicone

Strengths:

* open-source LLM observability
* sessions for grouped agent flows
* request-level monitoring

Weakness for our use case:

* LLM request/session focused
* less focused on agent-loop semantics

## 8.7 n8n

Strengths:

* visual workflow builder
* AI agent workflows
* execution history
* evaluations

Weakness for our use case:

* builder/orchestrator, not agent-loop debugger
* less useful for code-first agent developers

---

# 9. Product Gap

Existing tools answer:

> What happened in my LLM app?

LoopLens should answer:

> Is my agent loop healthy?

Existing tools show traces.

LoopLens should interpret traces through loop-specific questions:

* Did the agent repeat the same action?
* Did state improve?
* Did the same tool fail repeatedly?
* Did handoff cause duplicate work?
* Did retry change the input?
* Did cost grow without progress?
* Did a branch increase loop depth?
* Did the loop terminate properly?
* Which step should I fix?

---

# 10. Product Thesis

Agent development is becoming loop engineering.

As agents become longer-running, multi-step, and multi-agent, developers need loop observability, not just request observability.

The winning wedge is a small, local-first tool that gives instant value:

1. Run your agent.
2. Watch every step live.
3. See loop warnings immediately.
4. Export/share traces.
5. Fix the agent faster.

---

# 11. MVP Objective

Ship a working developer MVP quickly.

The MVP should prove this core claim:

> LoopLens can detect and explain an agent getting stuck in a repetitive loop while it is running.

---

# 12. MVP Scope

## In scope for MVP

* Python SDK
* local FastAPI server
* local SQLite storage
* CLI
* React web UI
* real-time event streaming
* run timeline
* metrics bar
* warnings panel
* simple loop detection
* JSONL import/export
* example agents
* README and demo video

## Out of scope for MVP

* hosted SaaS
* authentication
* team accounts
* billing
* enterprise dashboards
* full OpenTelemetry collector
* advanced graph visualization
* semantic embeddings
* LLM-based diagnosis
* full replay engine
* prompt versioning
* dataset evals
* production alerting
* complex RBAC

---

# 13. MVP User Journey

## Journey: Debug a looping agent

1. Developer installs LoopLens.

```bash
pip install looplens
```

2. Developer starts local LoopLens.

```bash
looplens dev
```

3. Developer instruments agent.

```python
from looplens import trace, event

with trace("research-agent"):
    event("agent_started", agent="researcher")
    event("tool_call_started", tool="web_search", input={"query": "AI agents"})
    event("tool_call_completed", tool="web_search", output={"results": 5})
```

4. Developer runs agent.

```bash
python agent.py
```

5. LoopLens UI opens.

```txt
http://localhost:8765
```

6. Developer sees live events.

7. Agent repeats same tool call.

8. LoopLens shows warning.

```txt
Possible loop detected:
web_search called 4 times with similar input and no state update.
```

9. Developer inspects timeline.

10. Developer fixes prompt, retry rule, or state update.

11. Developer reruns and compares manually.

---

# 14. Core Features

## 14.1 Python SDK

### Requirement

Provide a tiny SDK developers can add to any Python agent.

### API

```python
from looplens import trace, event

with trace("invoice-agent"):
    event("llm_call_started", model="gpt-4.1", agent="planner")
    event("llm_call_completed", model="gpt-4.1", tokens=800, cost=0.01)
    event("tool_call_started", tool="ocr_extract", input={"file": "invoice.pdf"})
    event("tool_call_completed", tool="ocr_extract", output={"pages": 2})
```

### SDK behavior

* creates run if not present
* assigns run_id
* assigns event_id
* assigns sequence number
* sends events to local server
* if server unavailable, writes JSONL locally
* should not crash user app if LoopLens fails
* should support environment variables

### Environment variables

```txt
LOOPLENS_ENDPOINT=http://localhost:8765
LOOPLENS_ENABLED=true
LOOPLENS_PROJECT=default
LOOPLENS_CAPTURE_INPUTS=true
LOOPLENS_CAPTURE_OUTPUTS=true
```

---

## 14.2 CLI

Command name:

```bash
looplens
```

### Required commands

```bash
looplens init
```

Creates local config.

```bash
looplens server
```

Starts FastAPI backend.

```bash
looplens ui
```

Starts frontend.

```bash
looplens dev
```

Starts backend and frontend together.

```bash
looplens watch traces/
```

Watches JSONL trace files and streams them into LoopLens.

```bash
looplens export <run_id>
```

Exports one run as JSONL.

```bash
looplens import <file.jsonl>
```

Imports a trace file.

```bash
looplens demo
```

Runs a sample looping agent that intentionally triggers warnings.

---

## 14.3 Backend Server

### Stack

* Python
* FastAPI
* SQLite
* Pydantic
* WebSocket or SSE
* Uvicorn

### Required API routes

```txt
POST /api/runs
GET  /api/runs
GET  /api/runs/{run_id}
POST /api/events
GET  /api/runs/{run_id}/events
GET  /api/runs/{run_id}/warnings
GET  /api/runs/{run_id}/metrics
GET  /api/health
WS   /ws/runs/{run_id}
```

### Backend responsibilities

* receive events
* validate schema
* store runs
* store events
* compute metrics
* run loop detectors
* store warnings
* stream new events to frontend
* export JSONL

---

## 14.4 Web UI

### Stack

* React
* Vite
* TypeScript
* Tailwind CSS
* shadcn/ui optional
* WebSocket client

### Screen 1: Runs List

Fields:

* run name
* status
* started at
* duration
* total steps
* model calls
* tool calls
* retries
* warnings
* cost
* tokens

### Screen 2: Run Detail

Sections:

1. Header

   * run name
   * status
   * duration
   * health score

2. Metrics bar

   * total steps
   * LLM calls
   * tool calls
   * retries
   * errors
   * total tokens
   * estimated cost

3. Timeline

   * event sequence
   * event type
   * agent
   * model/tool
   * latency
   * status
   * warning badge

4. Warning panel

   * repeated tool
   * retry storm
   * no-progress loop
   * cost spike
   * long step

5. Event detail drawer

   * raw JSON
   * input
   * output
   * error
   * metadata

6. Simple run summary

   * “Healthy”
   * “Warning”
   * “Likely stuck”

---

# 15. Event Schema

## 15.1 Base event

```json
{
  "event_id": "evt_123",
  "run_id": "run_123",
  "timestamp": "2026-06-27T12:00:00Z",
  "sequence": 1,
  "type": "tool_call_started",
  "agent": "researcher",
  "name": "web_search",
  "status": "started",
  "input": {},
  "output": {},
  "error": null,
  "metadata": {}
}
```

## 15.2 Required fields

* event_id
* run_id
* timestamp
* sequence
* type

## 15.3 Optional fields

* project
* agent
* name
* status
* model
* tool
* input
* output
* error
* tokens
* cost
* latency_ms
* parent_event_id
* span_id
* trace_id
* metadata

## 15.4 Event types

```txt
run_started
run_completed
run_failed

agent_started
agent_completed
agent_failed

llm_call_started
llm_call_completed
llm_call_failed

tool_call_started
tool_call_completed
tool_call_failed

state_updated
memory_read
memory_write

retry_triggered
handoff_started
handoff_completed
handoff_failed

guardrail_passed
guardrail_failed

loop_warning
cost_warning
error_warning
```

---

# 16. Warning Schema

```json
{
  "warning_id": "warn_123",
  "run_id": "run_123",
  "event_id": "evt_456",
  "type": "repeated_tool_call",
  "severity": "warning",
  "message": "web_search was called 4 times with similar input.",
  "details": {
    "tool": "web_search",
    "count": 4,
    "window": 8
  },
  "created_at": "2026-06-27T12:00:00Z"
}
```

Severity levels:

```txt
info
warning
critical
```

---

# 17. Loop Detection Rules

## Rule 1: Repeated tool call

Trigger when the same tool is called 3 or more times within a configurable window.

Default:

```txt
same tool >= 3 times within last 8 events
```

Warning:

```txt
Repeated tool call detected.
```

## Rule 2: Repeated tool call with similar input

Trigger when same tool is called with similar serialized input.

MVP similarity:

* normalize JSON
* stringify
* compare using SequenceMatcher or token overlap
* default threshold: 0.85

Warning:

```txt
Same tool called repeatedly with similar input.
```

## Rule 3: No-progress loop

Trigger when same tool or agent repeats and no `state_updated`, `memory_write`, or successful new output event happens between repeated calls.

Warning:

```txt
Possible no-progress loop detected.
```

## Rule 4: Retry storm

Trigger when `retry_triggered` appears 3 or more times in one run or 3 times in a short window.

Warning:

```txt
Retry storm detected.
```

## Rule 5: Long-running step

Trigger when latency exceeds threshold.

Default:

```txt
latency_ms > 30000
```

Warning:

```txt
Long-running step detected.
```

## Rule 6: Cost spike

Trigger when one event accounts for more than 50% of total run cost so far, after minimum cost threshold.

Default:

```txt
event_cost > 50% of total_cost_so_far and total_cost_so_far > $0.05
```

Warning:

```txt
Cost spike detected.
```

## Rule 7: Handoff bounce

Trigger when agents hand off back and forth repeatedly.

Example:

```txt
planner -> researcher -> planner -> researcher
```

Warning:

```txt
Possible handoff bounce detected.
```

This can be post-MVP if needed.

---

# 18. Metrics

## Run-level metrics

* total events
* total duration
* total LLM calls
* total tool calls
* total retries
* total handoffs
* total errors
* total tokens
* estimated cost
* average latency
* max latency
* most used tool
* most active agent
* warnings count
* loop health status

## Loop health status

```txt
Healthy
Warning
Likely stuck
Failed
```

### Simple scoring

Start at 100.

Subtract:

* repeated tool warning: -15
* similar input warning: -20
* retry storm: -20
* no-progress warning: -30
* long-running step: -10
* cost spike: -15
* failed run: -30

Score mapping:

```txt
80-100: Healthy
50-79: Warning
0-49: Likely stuck
```

---

# 19. Storage Design

Use SQLite for MVP.

## runs table

```sql
CREATE TABLE runs (
  id TEXT PRIMARY KEY,
  name TEXT,
  project TEXT,
  status TEXT,
  started_at TEXT,
  ended_at TEXT,
  total_cost REAL DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  metadata_json TEXT
);
```

## events table

```sql
CREATE TABLE events (
  id TEXT PRIMARY KEY,
  run_id TEXT,
  sequence INTEGER,
  timestamp TEXT,
  type TEXT,
  agent TEXT,
  name TEXT,
  status TEXT,
  model TEXT,
  tool TEXT,
  input_json TEXT,
  output_json TEXT,
  error_json TEXT,
  tokens INTEGER,
  cost REAL,
  latency_ms INTEGER,
  parent_event_id TEXT,
  span_id TEXT,
  trace_id TEXT,
  metadata_json TEXT
);
```

## warnings table

```sql
CREATE TABLE warnings (
  id TEXT PRIMARY KEY,
  run_id TEXT,
  event_id TEXT,
  type TEXT,
  severity TEXT,
  message TEXT,
  details_json TEXT,
  created_at TEXT
);
```

---

# 20. Technical Architecture

## MVP architecture

```txt
User Agent App
    |
    | LoopLens Python SDK
    v
Local LoopLens FastAPI Server
    |
    | store events
    v
SQLite
    |
    | WebSocket/SSE stream
    v
React UI
```

## Import architecture

```txt
JSONL trace file
    |
    | looplens import
    v
SQLite
    |
    v
React UI
```

## Watch mode

```txt
trace.jsonl
    |
    | file watcher
    v
LoopLens server
    |
    v
Live UI
```

---

# 21. Framework Integration Strategy

## MVP

Manual SDK instrumentation only.

This keeps the first version simple.

## V1 adapters

Add adapters in this order:

1. LangGraph
2. OpenAI Agents SDK
3. CrewAI
4. AutoGen
5. Pydantic AI
6. Generic OpenTelemetry/OpenInference import

## Why this order?

LangGraph is the most natural fit because its execution model is explicitly graph/state/loop-based.

OpenAI Agents SDK is important because it already exposes useful tracing concepts like tool calls, handoffs, guardrails, and custom events.

CrewAI is useful because multi-agent crews often create handoff/repetition problems.

Generic trace import prevents vendor lock-in.

---

# 22. Product Differentiation

## Not “another LangSmith”

LoopLens should not try to beat LangSmith at full observability, prompt management, or production monitoring.

## Not “another Langfuse”

LoopLens should not begin as a full evaluation and prompt-versioning platform.

## Not “another Phoenix”

LoopLens should not begin as a full OpenTelemetry observability backend.

## Core difference

LoopLens specializes in:

* loop diagnosis
* progress detection
* repeated-action detection
* agent trajectory health
* local-first debugging
* fast developer feedback

## Differentiation statement

Generic observability tools show spans.

LoopLens explains loop behavior.

---

# 23. MVP UX Principles

## 23.1 Timeline before graph

Do not build graph visualization first.

Graph views look impressive but take longer to build and can become confusing.

The first useful UI is:

```txt
Live timeline + warnings + metrics
```

## 23.2 Warnings should be opinionated

Do not just show raw logs.

Every warning should say:

* what happened
* why it matters
* where it happened
* possible fix

Example:

```txt
Possible no-progress loop detected.

validate_invoice was called 4 times with similar input.
No state_updated event occurred between calls.

Try:
- add max retry count
- update validation state after failure
- route to human after repeated failure
```

## 23.3 Local-first

The MVP should work without login, cloud, or API key.

## 23.4 Low-friction setup

A developer should see value in under 5 minutes.

## 23.5 Do not crash user apps

If LoopLens is down, SDK should fail silently and write local JSONL.

---

# 24. Build Plan

## Phase 0: Repo setup

Duration: half day

Deliverables:

* monorepo structure
* Python package
* backend folder
* frontend folder
* examples folder
* README skeleton

Repo structure:

```txt
looplens/
  README.md
  pyproject.toml

  looplens/
    __init__.py
    sdk.py
    cli.py
    config.py

    server/
      app.py
      db.py
      models.py
      routes.py
      detectors.py
      websocket.py
      metrics.py

  ui/
    package.json
    src/
      main.tsx
      App.tsx
      pages/
        RunsPage.tsx
        RunDetailPage.tsx
      components/
        MetricsBar.tsx
        Timeline.tsx
        WarningCard.tsx
        EventDrawer.tsx

  examples/
    simple_agent.py
    looping_agent.py
    retry_storm_agent.py

  traces/
    sample_run.jsonl
```

---

## Phase 1: Backend and database

Duration: 1 day

Build:

* FastAPI app
* SQLite schema
* create run
* ingest event
* list runs
* list events
* list warnings
* metrics endpoint

Acceptance:

```bash
looplens server
```

starts backend.

```bash
curl http://localhost:8765/api/health
```

returns healthy.

---

## Phase 2: SDK

Duration: 1 day

Build:

* `trace()` context manager
* `event()` function
* event ID generation
* run ID context
* HTTP send
* JSONL fallback
* config via env vars

Acceptance:

This works:

```python
from looplens import trace, event

with trace("demo-agent"):
    event("llm_call_started", model="gpt-4.1")
    event("llm_call_completed", model="gpt-4.1", tokens=500, cost=0.01)
```

---

## Phase 3: CLI

Duration: half day

Build:

* Typer CLI
* `looplens init`
* `looplens server`
* `looplens dev`
* `looplens import`
* `looplens export`
* `looplens demo`

Acceptance:

```bash
looplens demo
```

runs a sample agent and creates a trace.

---

## Phase 4: Frontend UI

Duration: 1.5 days

Build:

* Runs page
* Run detail page
* timeline
* metrics bar
* warning cards
* event drawer
* raw JSON view

Acceptance:

Developer can open UI and inspect a run.

---

## Phase 5: Real-time streaming

Duration: 1 day

Build:

* WebSocket/SSE route
* frontend live updates
* live metrics refresh
* live warning panel

Acceptance:

Events appear in UI while agent is running.

---

## Phase 6: Loop detection

Duration: 1 day

Build:

* repeated tool detector
* similar input detector
* no-progress detector
* retry storm detector
* long-step detector
* cost spike detector

Acceptance:

`looplens demo` intentionally triggers warning:

```txt
Possible no-progress loop detected.
```

---

## Phase 7: Polish and launch

Duration: 1 day

Build:

* README
* screenshots
* GIF/video
* example agents
* install instructions
* limitations section
* launch post

Acceptance:

A new developer can run the demo in under 5 minutes.

---

# 25. One-Week Shipping Plan

## Day 1

* repo setup
* FastAPI backend
* SQLite schema
* event ingestion

## Day 2

* SDK
* JSONL fallback
* simple example agent

## Day 3

* CLI
* import/export
* demo command

## Day 4

* React UI
* runs list
* run detail timeline

## Day 5

* real-time WebSocket/SSE
* live updates

## Day 6

* loop detection rules
* warning cards
* health score

## Day 7

* README
* demo video
* launch assets
* cleanup

---

# 26. Acceptance Criteria

The MVP is acceptable if:

1. `pip install -e .` works locally.
2. `looplens dev` starts backend and UI.
3. User can instrument a custom Python agent with fewer than 10 lines.
4. Events are stored in SQLite.
5. Events appear in UI in real time.
6. Timeline clearly shows LLM calls, tool calls, retries, and state updates.
7. Repeated tool-call detection works.
8. No-progress warning works.
9. Retry storm warning works.
10. Run metrics are visible.
11. JSONL export works.
12. Demo agent reliably triggers at least one loop warning.
13. README explains setup in under 5 minutes.

---

# 27. Example Demo Agent

The demo agent should intentionally repeat the same tool call.

```python
from looplens import trace, event
import time

def fake_search(query):
    event("tool_call_started", tool="web_search", input={"query": query})
    time.sleep(0.5)
    event("tool_call_completed", tool="web_search", output={"results": []})

with trace("looping-research-agent"):
    event("agent_started", agent="researcher")

    for i in range(5):
        event("llm_call_started", agent="researcher", model="demo-model")
        time.sleep(0.3)
        event("llm_call_completed", agent="researcher", model="demo-model", tokens=200, cost=0.002)
        fake_search("latest AI agent observability tools")

    event("agent_completed", agent="researcher", status="failed")
```

Expected warning:

```txt
Same tool called repeatedly with similar input.
Possible no-progress loop detected.
```

---

# 28. Launch Strategy

## Launch headline

```txt
I built LoopLens — Chrome DevTools for AI agent loops.
```

## Launch demo

Show a simple agent repeatedly calling the same search tool.

Before:

```txt
Terminal logs are noisy.
The agent looks like it is working.
```

After:

```txt
LoopLens detects:
- same tool called 5 times
- similar input repeated
- no state update
- wasted cost estimate
```

## Launch channels

* GitHub
* LinkedIn
* X/Twitter
* Hacker News
* Reddit r/LangChain
* Reddit r/LocalLLaMA
* Reddit r/AI_Agents
* LangGraph Discord
* CrewAI community
* OpenAI developer community

---

# 29. README Promise

The README should say:

```txt
LoopLens helps you debug AI agents that get stuck in loops.

It gives you:
- live timeline of agent execution
- LLM call and tool call visibility
- retry and handoff tracking
- token and cost metrics
- loop warnings
- JSONL import/export
- local-first UI
```

Quickstart:

```bash
pip install looplens
looplens dev
looplens demo
```

---

# 30. Future Roadmap

## V1

* LangGraph adapter
* OpenAI Agents SDK adapter
* CrewAI adapter
* better trace import
* run comparison
* simple graph view
* cost budget alerts

## V2

* semantic similarity with embeddings
* replay from step
* prompt change comparison
* tool output mutation testing
* LLM-based diagnosis
* OpenTelemetry collector support
* OpenInference compatibility

## V3

* hosted dashboard
* team workspaces
* production alerts
* Slack alerts
* trace sharing
* eval integration
* regression testing
* CI loop checks

---

# 31. Key Risks

## Risk 1: Too similar to LangSmith/Langfuse

Mitigation:

Focus messaging on loop debugging, not generic observability.

## Risk 2: Building too much

Mitigation:

No hosted SaaS, no auth, no evals, no graph-first UI in MVP.

## Risk 3: Manual instrumentation friction

Mitigation:

Start manual, then add LangGraph/OpenAI/CrewAI adapters.

## Risk 4: Loop detection too basic

Mitigation:

Make warnings transparent and rule-based. Do not overclaim intelligence.

## Risk 5: UI takes too long

Mitigation:

Use timeline-first UI. Avoid complex graph visualization initially.

---

# 32. Final MVP Definition

The first shippable LoopLens version is:

```txt
A local CLI + web UI that receives agent events, shows them live, and warns when the agent appears stuck in a repeated loop.
```

If it does only that well, it is worth shipping.

---

# 33. Claude Code Build Prompt

Build LoopLens, a local-first real-time debugger for AI agent loops.

Core product:
LoopLens helps developers see AI agent execution live and detects repeated loops, retry storms, no-progress behavior, and cost spikes.

Build an MVP with:

1. Python SDK

   * `trace(name)` context manager
   * `event(type, **kwargs)` function
   * sends events to local server
   * falls back to JSONL if server unavailable
   * never crashes user app

2. CLI using Typer

   * `looplens init`
   * `looplens server`
   * `looplens ui`
   * `looplens dev`
   * `looplens demo`
   * `looplens import <file>`
   * `looplens export <run_id>`

3. Backend

   * FastAPI
   * SQLite
   * Pydantic models
   * POST /api/runs
   * GET /api/runs
   * GET /api/runs/{run_id}
   * POST /api/events
   * GET /api/runs/{run_id}/events
   * GET /api/runs/{run_id}/warnings
   * GET /api/runs/{run_id}/metrics
   * WebSocket or SSE for real-time updates

4. Detection rules

   * repeated same tool 3+ times
   * same tool with similar input 3+ times
   * retry storm
   * long-running step
   * cost spike
   * no-progress loop when same tool repeats and no state update occurs

5. Frontend

   * React + Vite + TypeScript
   * runs list
   * run detail page
   * live timeline
   * metrics bar
   * warning cards
   * event detail drawer
   * raw JSON viewer

6. Examples

   * simple_agent.py
   * looping_agent.py
   * retry_storm_agent.py

Optimize for a working developer MVP over perfect architecture. Keep code clean and simple. Do not build hosted SaaS, auth, billing, eval datasets, or complex graph visualization yet.
