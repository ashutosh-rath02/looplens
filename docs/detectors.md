# Loop detectors

Detection is **rule-based and transparent** — no black-box scoring. On every
event the backend re-scans the run and raises (or updates) warnings. Each warning
says what happened, why it matters, and what to try.

## The nine rules

| Warning | Fires when |
| --- | --- |
| `repeated_tool_call` | same tool ≥3× within the last 8 **tool calls** (the window slides over tool calls, not raw events, so interleaved ReAct traces still trip it) |
| `repeated_tool_call_similar_input` | same tool ≥3× with ≥85% similar input |
| `repeated_tool_call_exact_input` | same tool ≥3× with **byte-identical** input — the highest-confidence repeat signal |
| `no_progress` | a tool repeats with no `state_updated` / `memory_write` between calls |
| `empty_result_loop` | a tool returns empty / "no results" ≥3× — the agent is looping on a dead end |
| `retry_storm` | `retry_triggered` ≥3× in the run |
| `long_running_step` | a step over 30s |
| `cost_spike` | one event > 50% of run cost so far (above a $0.05 floor) |
| `handoff_bounce` | control ping-pongs between the same two agents (A→B→A→B) |

The same loop can trip several rules at once — that's intended. Byte-identical
repeats, for instance, are also "similar" and usually show "no progress", and the
stacked penalties reflect higher confidence that the run is stuck.

## Health scoring

Each warning carries a penalty. A run starts at 100; penalties subtract from it,
and the score maps to a status:

| Warning | Penalty |
| --- | --- |
| `no_progress` | −30 |
| `repeated_tool_call_exact_input` | −25 |
| `repeated_tool_call_similar_input` | −20 |
| `empty_result_loop` | −20 |
| `retry_storm` | −20 |
| `handoff_bounce` | −20 |
| `repeated_tool_call` | −15 |
| `cost_spike` | −15 |
| `long_running_step` | −10 |
| (run ended in failure) | −30 |

| Score | Status |
| --- | --- |
| 80–100 | **Healthy** |
| 50–79 | **Warning** |
| 0–49 | **Likely stuck** |
| any, run failed | **Failed** |

## Notes and limits

- Detection is **rule-based, not semantic** — `similar_input` uses string
  similarity, not embeddings.
- Warnings are **deduplicated**: a single loop raises one warning that updates
  its count as the loop grows, rather than one warning per event.
- These rules work the same whether events arrive via
  [OpenTelemetry](opentelemetry.md), the [LangGraph adapter](langgraph.md), or
  the [manual SDK](sdk.md).
