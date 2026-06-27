"""Loop detection rules (PRD section 17).

``run_detectors`` is called by the ingestion route after every event. It scans
the run's events, compares against warnings already raised, and returns only the
*new* warning rows to store. Each warning is opinionated: what happened, why it
matters, and what to try (PRD section 23.2).

Rules:
  1. repeated_tool_call               — same tool >= 3x within the last 8 tool calls
  2. repeated_tool_call_similar_input — same tool >= 3x with near-identical input
  3. no_progress                      — tool repeats with no state/memory update
  4. retry_storm                      — retry_triggered >= 3x in the run
  5. long_running_step                — a step over the latency threshold
  6. cost_spike                       — one event dominating run cost
  7. handoff_bounce                   — two agents handing off back and forth
"""

from __future__ import annotations

import difflib
import json
import sqlite3
from collections import defaultdict

from . import db

REPEAT_WINDOW = 8
REPEAT_THRESHOLD = 3
SIMILARITY = 0.85
RETRY_THRESHOLD = 3
LATENCY_MS = 30_000
COST_MIN = 0.05


def _tool(e: sqlite3.Row) -> str | None:
    return e["tool"] or e["name"]


def _norm(input_json: str | None) -> str:
    if not input_json:
        return ""
    try:
        return json.dumps(json.loads(input_json), sort_keys=True)
    except (json.JSONDecodeError, TypeError):
        return input_json


# --- individual rules ------------------------------------------------------

def _repeated_tool(events):
    # Window over the last REPEAT_WINDOW *tool calls*, not raw events. A ReAct
    # step interleaves llm_call_* and tool_call_* events, so a raw-event window
    # only ever holds one or two tool calls and never trips the threshold. The
    # signal we want is "the same tool keeps getting called", so slide over the
    # tool-call sequence itself.
    tool_starts = [e for e in events if e["type"] == "tool_call_started" and _tool(e)]
    window = tool_starts[-REPEAT_WINDOW:]
    counts: dict[str, int] = defaultdict(int)
    last: dict[str, str] = {}
    for e in window:
        t = _tool(e)
        counts[t] += 1
        last[t] = e["id"]
    out = []
    for t, c in counts.items():
        if c >= REPEAT_THRESHOLD:
            out.append({
                "type": "repeated_tool_call", "severity": "warning",
                "message": (f"'{t}' was called {c} times within a window of {REPEAT_WINDOW} "
                            f"tool calls. Check the loop's exit condition or add a step limit."),
                "details": {"tool": t, "count": c, "window": REPEAT_WINDOW},
                "event_id": last[t],
            })
    return out


def _similar_input(events):
    groups: dict[str, list] = defaultdict(list)
    for e in events:
        if e["type"] == "tool_call_started" and _tool(e):
            groups[_tool(e)].append(e)
    out = []
    for t, evs in groups.items():
        if len(evs) < REPEAT_THRESHOLD:
            continue
        inputs = [_norm(e["input_json"]) for e in evs]
        ref = inputs[-1]
        similar = sum(1 for s in inputs if difflib.SequenceMatcher(None, ref, s).ratio() >= SIMILARITY)
        if similar >= REPEAT_THRESHOLD:
            out.append({
                "type": "repeated_tool_call_similar_input", "severity": "warning",
                "message": (f"'{t}' was called {similar} times with near-identical input "
                            f"(>= {int(SIMILARITY * 100)}% similar). The agent may be stuck "
                            f"repeating the same query — vary the input or break the loop."),
                "details": {"tool": t, "count": similar, "threshold": SIMILARITY},
                "event_id": evs[-1]["id"],
            })
    return out


def _no_progress(events):
    progress = {"state_updated", "memory_write"}
    groups: dict[str, list[int]] = defaultdict(list)
    for i, e in enumerate(events):
        if e["type"] == "tool_call_started" and _tool(e):
            groups[_tool(e)].append(i)
    out = []
    for t, idxs in groups.items():
        if len(idxs) < REPEAT_THRESHOLD:
            continue
        between = events[idxs[0]:idxs[-1] + 1]
        if not any(e["type"] in progress for e in between):
            out.append({
                "type": "no_progress", "severity": "critical",
                "message": (f"'{t}' repeated {len(idxs)} times with no state_updated or "
                            f"memory_write in between — the loop isn't making progress. "
                            f"Update state after each attempt, or route to a human after N tries."),
                "details": {"tool": t, "count": len(idxs)},
                "event_id": events[idxs[-1]]["id"],
            })
    return out


def _retry_storm(events):
    retries = [e for e in events if e["type"] == "retry_triggered"]
    if len(retries) >= RETRY_THRESHOLD:
        return [{
            "type": "retry_storm", "severity": "warning",
            "message": (f"{len(retries)} retries were triggered in this run. Retrying without "
                        f"changing the input rarely helps — change strategy, add backoff, or cap retries."),
            "details": {"count": len(retries)},
            "event_id": retries[-1]["id"],
        }]
    return []


def _long_step(events):
    out = []
    for e in events:
        lat = e["latency_ms"]
        if lat is not None and lat > LATENCY_MS:
            label = _tool(e) or e["type"]
            out.append({
                "type": "long_running_step", "severity": "info",
                "message": f"A step took {lat} ms (> {LATENCY_MS} ms). Investigate the slow '{label}' call.",
                "details": {"event_id": e["id"], "latency_ms": lat, "threshold": LATENCY_MS},
                "event_id": e["id"],
            })
    return out


def _cost_spike(events):
    out = []
    running = 0.0
    for e in events:
        c = e["cost"]
        if c:
            running += c
            if running > COST_MIN and c > 0.5 * running:
                out.append({
                    "type": "cost_spike", "severity": "warning",
                    "message": (f"One step cost ${c:.4f}, over half the run's ${running:.4f} so far. "
                                f"A single call is dominating spend — check tokens/model for that step."),
                    "details": {"event_id": e["id"], "event_cost": round(c, 6),
                                "total_so_far": round(running, 6)},
                    "event_id": e["id"],
                })
    return out


def _handoff_bounce(events):
    # Multi-agent oscillation: control ping-pongs between the same two agents
    # (planner -> researcher -> planner -> researcher). The `agent` on each
    # handoff_started is the agent receiving control; an alternation between
    # exactly two agents is the bounce, regardless of source/target convention.
    agents = [e["agent"] for e in events
              if e["type"] == "handoff_started" and e["agent"]]
    last = [e["id"] for e in events if e["type"] == "handoff_started" and e["agent"]]
    if len(agents) < REPEAT_THRESHOLD:
        return []
    tail = agents[-6:]
    pair = set(tail)
    alternating = len(pair) == 2 and all(tail[i] != tail[i + 1] for i in range(len(tail) - 1))
    if not (alternating and len(tail) >= REPEAT_THRESHOLD):
        return []
    a, b = sorted(pair)
    return [{
        "type": "handoff_bounce", "severity": "warning",
        "message": (f"Agents '{a}' and '{b}' handed off back and forth {len(tail)} times "
                    f"without resolving. A handoff loop usually means neither agent can "
                    f"finish — clarify ownership, pass more context, or cap handoffs."),
        "details": {"agents": [a, b], "pair": f"{a}|{b}", "count": len(tail)},
        "event_id": last[-1],
    }]


_RULES = (_repeated_tool, _similar_input, _no_progress, _retry_storm, _long_step,
          _cost_spike, _handoff_bounce)


# --- engine ----------------------------------------------------------------

def _key(wtype: str, details: dict) -> str:
    """Stable identity so a warning is raised once, not on every later event."""
    discriminator = details.get("tool") or details.get("pair") or details.get("event_id") or ""
    return f"{wtype}|{discriminator}"


def run_detectors(conn: sqlite3.Connection, run_id: str) -> None:
    """Raise new warnings and refresh existing ones in place.

    A warning is identified by ``_key`` so it is raised once; if the same loop
    keeps growing we bump its count/message instead of spamming duplicates.
    """
    events = db.list_events(conn, run_id)
    by_key = {
        _key(w["type"], json.loads(w["details_json"] or "{}")): w
        for w in db.list_warnings(conn, run_id)
    }
    handled: set[str] = set()
    for rule in _RULES:
        for cand in rule(events):
            k = _key(cand["type"], cand["details"])
            if k in handled:
                continue
            handled.add(k)
            details_json = json.dumps(cand["details"])
            existing = by_key.get(k)
            if existing is None:
                db.insert_warning(conn, {
                    "id": db.gen_id("warn"),
                    "run_id": run_id,
                    "event_id": cand.get("event_id"),
                    "type": cand["type"],
                    "severity": cand["severity"],
                    "message": cand["message"],
                    "details_json": details_json,
                    "created_at": db.now_iso(),
                })
                continue
            # Already raised — bump count/message if the loop grew.
            old_count = json.loads(existing["details_json"] or "{}").get("count")
            new_count = cand["details"].get("count")
            if new_count is not None and (old_count is None or new_count > old_count):
                db.update_warning(conn, existing["id"], cand["message"], details_json)
