# MCP server

LoopLens ships an [MCP](https://modelcontextprotocol.io/) server so your **AI
coding agent** — Claude Code, Cursor, Windsurf, or anything that speaks the Model
Context Protocol — can ask LoopLens about your agent's loops without you leaving
the editor:

> **You:** did my last agent run loop?
>
> **Assistant (via LoopLens MCP):** Yes — run `loop` is **Likely stuck**:
> `web_search` repeated 4× with no progress. The culprit is event `evt_…` at
> step 7.

It is **read-only**. The MCP server reads the same local SQLite store the
dashboard and SDK already populate, reuses the same health scoring, and returns
the same verdict you see in the UI — there is no second capture path and no new
data leaves your machine.

## Install & run

```bash
pip install "looplens[mcp]"
looplens mcp        # serves over stdio (the default MCP transport)
```

`looplens mcp` blocks and talks MCP over stdin/stdout, so you normally don't run
it by hand — you point an MCP client at it (below).

## Connect a client

Most MCP clients take a command to launch the server. Add LoopLens like any other
stdio MCP server:

=== "Claude Code"

    ```bash
    claude mcp add looplens -- looplens mcp
    ```

=== "Generic `mcpServers` config (Cursor, Claude Desktop, …)"

    ```json
    {
      "mcpServers": {
        "looplens": {
          "command": "looplens",
          "args": ["mcp"]
        }
      }
    }
    ```

If LoopLens stores its database somewhere non-default, pass it through the same
`LOOPLENS_DB_PATH` environment variable the server uses, so the MCP server reads
the right file:

```json
{
  "mcpServers": {
    "looplens": {
      "command": "looplens",
      "args": ["mcp"],
      "env": { "LOOPLENS_DB_PATH": "/path/to/looplens.db" }
    }
  }
}
```

## Tools

All tools are read-only.

| Tool | What it answers |
| --- | --- |
| `list_runs(limit=20)` | Which recent runs are healthy vs. stuck? (health score + status per run) |
| `latest_run_diagnosis()` | Did my **most recent** run loop, and where? |
| `get_run_diagnosis(run_id)` | The verdict + every loop warning for a specific run |
| `get_run_warnings(run_id)` | The raw loop warnings (type, message, **culprit `event_id`**, details) |
| `get_run_metrics(run_id)` | Tokens, cost, latency, counts, and the health score |
| `get_run_events(run_id, limit=100)` | The event timeline, to inspect the loop itself |

The diagnosis tools return the same one-line verdict as the dashboard headline
(e.g. *"Likely stuck — 'search' repeated 5× with no progress. (+2 more
signals)"*), and every warning carries the `event_id` of the offending event, so
the assistant can point you straight at the line to fix.

## How it fits

The MCP server is a **consumption** path, not a capture path: you still get your
agent's events into LoopLens the usual way (the
[OpenTelemetry receiver](opentelemetry.md), an [adapter](frameworks.md), or the
[manual SDK](sdk.md)). MCP just makes the resulting loop verdicts available to
the AI assistant you're already building with.
