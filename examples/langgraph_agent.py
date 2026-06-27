"""A real LangGraph ReAct agent, auto-instrumented with LoopLens — no event() calls.

This is the LangGraph adapter (PRD section 21) in action: you pass ONE callback
handler in the run config and LoopLens captures every node's LLM and tool calls
automatically. No manual `trace()` / `event()` anywhere in your agent.

The `search` tool only knows a tiny corpus that lacks the answer, so the agent
tends to keep searching the same way — exactly the loop LoopLens flags
(repeated_tool_call / repeated_tool_call_exact_input / no_progress).

Requires:
    pip install 'looplens[langgraph]' langchain-openai
    export OPENAI_API_KEY=sk-...        (optionally OPENAI_MODEL)

Run `looplens dev` first to watch it live, then:
    PYTHONPATH=. python examples/langgraph_agent.py
"""

import os

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from looplens.integrations.langgraph import LoopLensCallbackHandler

CORPUS = {
    "install.md": "Install with pip install ourtool. Requires Python 3.10+.",
    "auth.md": "Authenticate by setting OURTOOL_TOKEN in the environment.",
    "deploy.md": "Deploy with `ourtool deploy`; it builds a container and pushes it.",
    "logs.md": "Stream logs with `ourtool logs -f`.",
    "uninstall.md": "Remove with pip uninstall ourtool.",
}
# Deliberately not covered by the corpus, so the agent keeps searching.
QUESTION = "What retry backoff strategy does ourtool use for failed deploys?"


@tool
def search(query: str) -> str:
    """Search the ourtool documentation for a query."""
    q = query.lower()
    hits = [
        f"{name}: {text}"
        for name, text in CORPUS.items()
        if any(word in text.lower() or word in name for word in q.split())
    ]
    return "\n".join(hits) if hits else "No results found."


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY to run this example.")

    model = ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    agent = create_react_agent(model, [search])

    # The whole integration: one handler, passed in the run config.
    handler = LoopLensCallbackHandler(name="langgraph-research-agent")
    result = agent.invoke(
        {"messages": [("user", QUESTION)]},
        config={"callbacks": [handler], "recursion_limit": 12},
    )
    print("\n--- agent answer ---")
    print(result["messages"][-1].content)
    print("\nOpen the LoopLens dashboard to inspect the run and any loop warnings.")


if __name__ == "__main__":
    main()
