"""A REAL OpenAI agent loop, instrumented with LoopLens.

This is not a synthetic event emitter. It makes real OpenAI Chat Completions
calls with function calling; the model genuinely decides whether to search
again. The `search` tool is deliberately limited — a tiny in-memory corpus that
does NOT contain the answer — so a capable model tends to retry the same search
with reworded queries. That produces a real repeated-tool / no-progress loop for
LoopLens to detect, with real tokens, real cost, and real latency.

Requires:
  pip install openai
  OPENAI_API_KEY in the environment  (set it, then restart so this process
                                      inherits it — Windows children inherit the
                                      env block from when the parent started)
  OPENAI_MODEL   (optional; default "gpt-4o-mini" — set to gpt-4o / o4-mini /
                  gpt-5 / etc. for your account)
  AGENT_MAX_STEPS (optional; default 8 — the loop's hard ceiling)

Run the LoopLens dashboard first:
  python -m looplens.server
Then (from the repo root):
  PYTHONPATH=. python examples/real_research_agent_openai.py
"""

from __future__ import annotations

import json
import os
import time

from openai import OpenAI

from looplens import event, flush, trace

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
MAX_STEPS = int(os.environ.get("AGENT_MAX_STEPS", "8"))

# Approximate USD per 1M tokens (input, output). Tokens are always exact (from
# the API); cost is derived from this editable table — adjust for your model.
PRICING = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "o4-mini": (1.10, 4.40),
}

# A tiny knowledge base. Note: nothing here mentions retries or backoff — the
# question below cannot be answered from it, which is what provokes the loop.
CORPUS = {
    "install.md": "Nimbus CLI: install with `pip install nimbus-cli`. Verify with `nimbus --version`.",
    "auth.md": "Run `nimbus login` to authenticate. Tokens live in ~/.nimbus/credentials.",
    "deploy.md": "Deploy with `nimbus deploy <app>`. Use --env to target staging or production.",
    "logs.md": "Stream logs with `nimbus logs <app> --follow`. Filter with --since and --level.",
    "uninstall.md": "Remove Nimbus CLI with `pip uninstall nimbus-cli` and delete ~/.nimbus.",
}


def search(query: str) -> dict:
    """Flaky/limited search: case-insensitive substring match over the corpus."""
    q = (query or "").lower().strip()
    hits = [name for name, text in CORPUS.items() if q and q in text.lower()]
    if not hits:
        return {"results": [], "note": "No documents matched that query."}
    return {"results": [{"doc": h, "text": CORPUS[h]} for h in hits]}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search the Nimbus CLI documentation for a query string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "what to look for"}
                },
                "required": ["query"],
            },
        },
    }
]

SYSTEM = (
    "You are a documentation assistant for the Nimbus CLI. Answer the user's "
    "question using ONLY the `search` tool to find supporting docs — do not "
    "answer from prior knowledge. Keep trying different search queries until you "
    "find the answer, then give it. Only say you cannot find it as a last resort."
)
QUESTION = "How do I configure a custom retry backoff strategy in the Nimbus CLI?"


def _cost(tokens_in: int, tokens_out: int) -> float:
    pin, pout = PRICING.get(MODEL, (0.0, 0.0))
    return round(tokens_in / 1e6 * pin + tokens_out / 1e6 * pout, 6)


def run() -> None:
    client = OpenAI()  # reads OPENAI_API_KEY from the environment
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": QUESTION},
    ]

    with trace("real-research-agent (openai)"):
        event("agent_started", agent="researcher",
              metadata={"model": MODEL, "question": QUESTION, "max_steps": MAX_STEPS})

        for step in range(MAX_STEPS):
            event("llm_call_started", agent="researcher", model=MODEL)
            t0 = time.perf_counter()
            resp = client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto",
            )
            latency_ms = int((time.perf_counter() - t0) * 1000)
            u = resp.usage
            event(
                "llm_call_completed", agent="researcher", model=MODEL,
                tokens=u.total_tokens, cost=_cost(u.prompt_tokens, u.completion_tokens),
                latency_ms=latency_ms,
                metadata={"prompt_tokens": u.prompt_tokens,
                          "completion_tokens": u.completion_tokens},
            )

            msg = resp.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                event("agent_completed", agent="researcher", status="completed",
                      output={"answer": msg.content})
                print(f"\nFinal answer after {step + 1} step(s):\n{msg.content}")
                return

            for call in msg.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                query = args.get("query", "")
                event("tool_call_started", tool="search", input={"query": query})
                result = search(query)
                event("tool_call_completed", tool="search",
                      output={"hit_count": len(result["results"])})
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result),
                })

        event("agent_completed", agent="researcher", status="failed",
              metadata={"reason": f"hit MAX_STEPS={MAX_STEPS} without answering"})
        print(f"\nGave up after {MAX_STEPS} steps without a confident answer.")


if __name__ == "__main__":
    run()
    flush(timeout=5)
