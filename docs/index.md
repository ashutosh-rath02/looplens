# LoopLens

**Chrome DevTools for AI agent loops.** A local-first, real-time debugger that
shows your agent's execution live and warns when it repeats itself, burns
tokens, retries blindly, or stops making progress.

[![PyPI](https://img.shields.io/pypi/v/looplens.svg)](https://pypi.org/project/looplens/)
[![Python](https://img.shields.io/pypi/pyversions/looplens.svg)](https://pypi.org/project/looplens/)
[![CI](https://github.com/ashutosh-rath02/looplens/actions/workflows/ci.yml/badge.svg)](https://github.com/ashutosh-rath02/looplens/actions/workflows/ci.yml)

LoopLens gives you:

- a live timeline of agent execution
- LLM-call and tool-call visibility
- retry and handoff tracking
- token and cost metrics
- loop warnings (repeated tool, no-progress, retry storm, cost spike, …)
- JSONL import/export
- a local-first UI — no login, no cloud, no API key

## See it in action

A looping agent calls `web_search` over and over. As events stream in live, the
metrics climb and LoopLens flags **Repeated tool call** and **No-progress loop**
— the warning counts track the repeat count in real time, and the health score
drops to *Warning*.

![LoopLens detecting a loop live](media/looplens-live-loop-detection.gif)

## Three ways to capture your agent

You don't have to rebuild your agent inside LoopLens. Pick whichever fits:

| Approach | Code in your agent | Best for |
| --- | --- | --- |
| [OpenTelemetry](opentelemetry.md) | none | any framework with an OTel instrumentor |
| [LangGraph adapter](langgraph.md) | one callback handler | LangGraph / LangChain |
| [Manual SDK](sdk.md) | `trace()` / `event()` / `@observe` | hand-rolled loops, full control |

## Next steps

- [Install LoopLens](installation.md)
- [Quickstart](quickstart.md) — dashboard up and a demo loop in three commands
- [How loop detection works](detectors.md)
