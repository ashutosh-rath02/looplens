// Small formatting + color helpers shared across the UI.

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
  if (type.startsWith("run_") || type.startsWith("agent_")) return "text-slate-400";
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
