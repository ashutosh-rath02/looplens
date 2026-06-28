// Small formatting + color helpers shared across the UI.

import { Metrics, WarningOut } from "./api";

// Most-diagnostic warning first — used to pick the headline cause.
const WARNING_PRIORITY = [
  "no_progress",
  "empty_result_loop",
  "repeated_tool_call_exact_input",
  "repeated_tool_call_similar_input",
  "repeated_tool_call",
  "handoff_bounce",
  "retry_storm",
  "cost_budget_exceeded",
  "cost_spike",
  "long_running_step",
];

function warningPhrase(w: WarningOut): string {
  const d = (w.details ?? {}) as Record<string, any>;
  const tool = d.tool as string | undefined;
  const count = d.count as number | undefined;
  switch (w.type) {
    case "no_progress":
      return `'${tool}' repeated ${count}× with no progress`;
    case "empty_result_loop":
      return `'${tool}' returned no results ${count}×`;
    case "repeated_tool_call_exact_input":
      return `'${tool}' called ${count}× with identical input`;
    case "repeated_tool_call_similar_input":
      return `'${tool}' called ${count}× with near-identical input`;
    case "repeated_tool_call":
      return `'${tool}' called ${count}× in a loop`;
    case "handoff_bounce":
      return `agents ${((d.agents as string[]) ?? []).join(" / ")} handed off ${d.count}× without resolving`;
    case "retry_storm":
      return `${d.count ?? "several"} retries fired without changing strategy`;
    case "cost_budget_exceeded":
      return "run cost crossed the configured budget";
    case "cost_spike":
      return "one step dominated the run's cost";
    case "long_running_step":
      return "a step ran far longer than expected";
    default:
      return warningTitle(w.type).toLowerCase();
  }
}

export function diagnose(
  warnings: WarningOut[],
  metrics: Metrics | null,
  status: string | null
): { text: string; tone: "good" | "warn" | "bad" } | null {
  if (!metrics) return null;
  if (status === "failed") return { text: "This run failed.", tone: "bad" };
  if (warnings.length === 0) {
    return { text: "No loops detected — this run looks healthy.", tone: "good" };
  }
  const rank = (t: string) => {
    const i = WARNING_PRIORITY.indexOf(t);
    return i === -1 ? 99 : i;
  };
  const primary = [...warnings].sort((a, b) => rank(a.type) - rank(b.type))[0];
  const more = warnings.length - 1;
  const suffix = more > 0 ? ` (+${more} more signal${more > 1 ? "s" : ""})` : "";
  const tone = metrics.loop_health_status === "Likely stuck" ? "bad" : "warn";
  return { text: `${metrics.loop_health_status} — ${warningPhrase(primary)}.${suffix}`, tone };
}

const WARNING_TITLES: Record<string, string> = {
  repeated_tool_call: "Repeated tool call",
  repeated_tool_call_similar_input: "Repeated tool call · similar input",
  repeated_tool_call_exact_input: "Repeated tool call · exact input",
  no_progress: "No-progress loop",
  empty_result_loop: "Empty-result loop",
  retry_storm: "Retry storm",
  long_running_step: "Long-running step",
  cost_spike: "Cost spike",
  cost_budget_exceeded: "Cost budget exceeded",
  handoff_bounce: "Handoff bounce",
};

export function warningTitle(type: string): string {
  return WARNING_TITLES[type] ?? type;
}

export function healthClasses(status: string | null | undefined): string {
  switch (status) {
    case "Healthy":
      return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
    case "Warning":
      return "bg-amber-500/15 text-amber-300 border-amber-500/30";
    case "Likely stuck":
      return "bg-rose-500/15 text-rose-300 border-rose-500/30";
    case "Failed":
      return "bg-rose-600/20 text-rose-300 border-rose-600/40";
    default:
      return "bg-slate-500/15 text-slate-300 border-slate-500/30";
  }
}

export function severityClasses(sev: string): string {
  switch (sev) {
    case "critical":
      return "bg-rose-500/10 border-rose-500/40 text-rose-200";
    case "warning":
      return "bg-amber-500/10 border-amber-500/40 text-amber-200";
    default:
      return "bg-sky-500/10 border-sky-500/40 text-sky-200";
  }
}

// Color a timeline row by event family.
export function eventColor(type: string): string {
  if (type.endsWith("_failed")) return "text-rose-300";
  if (type.startsWith("llm_call")) return "text-violet-300";
  if (type.startsWith("tool_call")) return "text-sky-300";
  if (type.startsWith("retry")) return "text-amber-300";
  if (type.startsWith("handoff")) return "text-fuchsia-300";
  if (type.startsWith("guardrail")) return "text-orange-300";
  if (type.startsWith("agent_")) return "text-cyan-300";
  if (type.startsWith("run_")) return "text-slate-400";
  if (type.startsWith("state_") || type.startsWith("memory_")) return "text-emerald-300";
  return "text-slate-300";
}

export function fmtDuration(sec: number | null | undefined): string {
  if (!sec) return "—";
  if (sec < 1) return `${Math.round(sec * 1000)}ms`;
  if (sec < 60) return `${sec.toFixed(1)}s`;
  const m = Math.floor(sec / 60);
  return `${m}m ${Math.round(sec % 60)}s`;
}

export function fmtCost(cost: number | null | undefined): string {
  if (!cost) return "$0";
  return `$${cost.toFixed(cost < 0.01 ? 4 : 2)}`;
}

export function fmtTime(ts: string | null | undefined): string {
  if (!ts) return "—";
  const d = new Date(ts);
  return isNaN(d.getTime()) ? "—" : d.toLocaleString();
}
