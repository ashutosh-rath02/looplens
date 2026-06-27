# CLI reference

The CLI ships with the `[server]` extra. Run `looplens --help` for the full list.

| Command | What it does |
| --- | --- |
| `looplens dev` | Start the backend + prebuilt UI and open the dashboard. `--no-open` to skip the browser; `--host` / `--port` to override. |
| `looplens server` | Start just the FastAPI backend (no browser). |
| `looplens demo` | Run a sample looping agent that trips a warning. |
| `looplens doctor` | Diagnose setup: server reachability, a real SDK→server round-trip, and JSONL fallback writability. Exits non-zero if any check fails. |
| `looplens init` | Write a local config template (`looplens.env`) and the JSONL fallback dir. |
| `looplens import <file.jsonl>` | Import a JSONL trace file into the dashboard. |
| `looplens export <run_id> [-o file]` | Export one run's events as JSONL. |
| `looplens watch <dir>` | Watch a directory of JSONL trace files and stream them in live. |

## `looplens doctor`

The fastest way to confirm a setup works end to end:

```text
$ looplens doctor
LoopLens doctor - endpoint http://127.0.0.1:8765
  [ok]   server reachable (version 0.1.0)
  [ok]   SDK round-trip - 4 events delivered (run looplens-doctor-ad3a37d0)
  [ok]   JSONL fallback writable (looplens-traces)
All checks passed.
```

If the server isn't running it reports `[FAIL] server not reachable` and exits
`1`, so onboarding never silently fails.

## Configuration

All commands read the same environment variables as the
[SDK](quickstart.md#configuration), plus server-side ones:

```bash
LOOPLENS_HOST=127.0.0.1
LOOPLENS_PORT=8765
LOOPLENS_DB_PATH=looplens.db
```
