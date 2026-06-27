import { ReactNode } from "react";
import { Metrics } from "../api";
import { fmtCost, fmtDuration } from "../lib";

function Tile({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="bg-panel/60 border border-edge rounded-lg px-3 py-2 min-w-[88px]">
      <div className="text-[11px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className="text-lg font-semibold text-slate-100 tabular-nums">{value}</div>
    </div>
  );
}

export default function MetricsBar({ m }: { m: Metrics | null }) {
  if (!m) return null;
  return (
    <div className="flex flex-wrap gap-2">
      <Tile label="Steps" value={m.total_events} />
      <Tile label="LLM" value={m.total_llm_calls} />
      <Tile label="Tools" value={m.total_tool_calls} />
      <Tile label="Retries" value={m.total_retries} />
      <Tile label="Errors" value={m.total_errors} />
      <Tile label="Tokens" value={m.total_tokens} />
      <Tile label="Cost" value={fmtCost(m.estimated_cost)} />
      <Tile label="Duration" value={fmtDuration(m.total_duration_sec)} />
      <Tile label="Avg latency" value={`${Math.round(m.average_latency_ms)}ms`} />
    </div>
  );
}
