# Quickstart

Get the dashboard running and watch a loop get flagged in three commands.

```bash
pip install "looplens[server]"
looplens dev      # start backend + prebuilt UI, opens http://localhost:8765
looplens demo     # run a sample looping agent that trips a warning
```

`looplens dev` opens the dashboard in your browser automatically (pass
`--no-open` to skip). If it doesn't, open <http://localhost:8765> yourself and
watch the run appear live.

## Instrument your own agent

The smallest possible integration with the [manual SDK](sdk.md):

```python
from looplens import trace, event

with trace("research-agent"):
    event("tool_call_started", tool="web_search", input={"query": "AI agents"})
    event("tool_call_completed", tool="web_search", output={"results": 5})
```

Or capture inputs, outputs, latency, and errors automatically:

```python
from looplens import observe

@observe(kind="tool")
def web_search(query):
    ...
```

Already on a framework? You usually don't need any of this — see
[framework integration](frameworks.md) to capture runs with **no LoopLens code
in your agent**.

## Configuration

The SDK is configured entirely via environment variables:

```bash
LOOPLENS_ENDPOINT=http://127.0.0.1:8765   # where the dashboard listens
LOOPLENS_ENABLED=true                      # set false to make the SDK a no-op
LOOPLENS_PROJECT=default
LOOPLENS_CAPTURE_INPUTS=true
LOOPLENS_CAPTURE_OUTPUTS=true
LOOPLENS_TRACE_DIR=looplens-traces         # JSONL fallback location
```

Events are sent from a background thread, so your loop never blocks. If the
dashboard is running, events stream to it live; if not, the SDK buffers them to a
local JSONL file and **never crashes your app**.
