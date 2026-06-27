# Manual SDK

The base SDK is **pure-stdlib with zero third-party dependencies**. Use it for
hand-rolled loops, frameworks without an instrumentor, or whenever you want to
emit exactly the events you care about.

## `trace()` and `event()`

`trace()` brackets a run; `event()` records a single agent event inside it.

```python
from looplens import trace, event

with trace("research-agent"):
    event("tool_call_started", tool="web_search", input={"query": "AI agents"})
    event("tool_call_completed", tool="web_search", output={"results": 5})
```

`event()` is safe to call and **never raises** — if the dashboard isn't running,
events buffer to a local JSONL file instead.

### Common event types

The [detectors](detectors.md) understand these out of the box:

- `llm_call_started` / `llm_call_completed` / `llm_call_failed`
- `tool_call_started` / `tool_call_completed` / `tool_call_failed`
- `retry_triggered`
- `handoff_started` (with `agent=` — the agent receiving control)
- `state_updated` / `memory_write` (progress signals)

Useful fields: `tool`, `model`, `agent`, `input`, `output`, `tokens`, `cost`,
`latency_ms`, `status`, `error`. Anything else you pass is folded into
`metadata`, so nothing is dropped.

## `@observe`

Wrap a function to capture its inputs, outputs, latency, and errors as a
started/completed event pair automatically:

```python
from looplens import observe

@observe(kind="tool")
def web_search(query):
    ...
```

Use `kind="llm"` for model calls. Errors are recorded as a `*_failed` event and
re-raised.

## `flush()`

Events are delivered from a background thread. `flush()` blocks until the queue
drains (it also runs automatically at process exit), which matters for
short-lived scripts:

```python
from looplens import flush
flush(timeout=5)
```

## No-op switch

Set `LOOPLENS_ENABLED=false` to turn every SDK call into a no-op — handy for
production or CI where you don't want any capture overhead.
