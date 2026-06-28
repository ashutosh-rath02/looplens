import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  getMetrics,
  getRun,
  getWarnings,
  listRuns,
  Metrics,
  RunOut,
  RunSummary,
  WarningOut,
} from "../api";
import { fmtCost, fmtDuration, healthClasses, warningTitle } from "../lib";

interface Side {
  run: RunOut;
  metrics: Metrics;
  warnings: WarningOut[];
}

const ROWS: {
  label: string;
  pick: (m: Metrics) => number;
  fmt: (n: number) => string;
  higherBetter?: boolean;
}[] = [
  { label: "Health score", pick: (m) => m.health_score, fmt: (n) => `${n}`, higherBetter: true },
  { label: "Steps", pick: (m) => m.total_events, fmt: (n) => `${n}` },
  { label: "LLM calls", pick: (m) => m.total_llm_calls, fmt: (n) => `${n}` },
  { label: "Tool calls", pick: (m) => m.total_tool_calls, fmt: (n) => `${n}` },
  { label: "Retries", pick: (m) => m.total_retries, fmt: (n) => `${n}` },
  { label: "Handoffs", pick: (m) => m.total_handoffs, fmt: (n) => `${n}` },
  { label: "Errors", pick: (m) => m.total_errors, fmt: (n) => `${n}` },
  { label: "Tokens", pick: (m) => m.total_tokens, fmt: (n) => `${n}` },
  { label: "Cost", pick: (m) => m.estimated_cost, fmt: fmtCost },
  { label: "Duration", pick: (m) => m.total_duration_sec, fmt: fmtDuration },
  { label: "Warnings", pick: (m) => m.warnings_count, fmt: (n) => `${n}` },
];

function Delta({
  a,
  b,
  fmt,
  higherBetter,
}: {
  a: number;
  b: number;
  fmt: (n: number) => string;
  higherBetter?: boolean;
}) {
  const d = b - a;
  if (d === 0) return <span className="text-slate-600">—</span>;
  const better = higherBetter ? d > 0 : d < 0;
  return (
    <span className={better ? "text-emerald-400" : "text-rose-400"}>
      {d > 0 ? "▲" : "▼"} {fmt(Math.abs(d))}
    </span>
  );
}

function HealthBadge({ m }: { m: Metrics }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${healthClasses(m.loop_health_status)}`}>
      {m.loop_health_status} · {m.health_score}
    </span>
  );
}

export default function ComparePage() {
  const [params, setParams] = useSearchParams();
  const a = params.get("a");
  const b = params.get("b");

  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [left, setLeft] = useState<Side | null>(null);
  const [right, setRight] = useState<Side | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selA, setSelA] = useState(a ?? "");
  const [selB, setSelB] = useState(b ?? "");

  useEffect(() => {
    listRuns()
      .then(setRuns)
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!a || !b) {
      setLeft(null);
      setRight(null);
      return;
    }
    let alive = true;
    const load = async (id: string): Promise<Side> => {
      const [run, metrics, warnings] = await Promise.all([
        getRun(id),
        getMetrics(id),
        getWarnings(id),
      ]);
      return { run, metrics, warnings };
    };
    Promise.all([load(a), load(b)])
      .then(([l, r]) => {
        if (alive) {
          setLeft(l);
          setRight(r);
          setError(null);
        }
      })
      .catch((e) => alive && setError(String(e)));
    return () => {
      alive = false;
    };
  }, [a, b]);

  const compare = () => {
    if (selA && selB) setParams({ a: selA, b: selB });
  };

  const aTypes = new Set((left?.warnings ?? []).map((w) => w.type));
  const bTypes = new Set((right?.warnings ?? []).map((w) => w.type));
  const warningTypes = Array.from(new Set([...aTypes, ...bTypes])).sort();

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-100 mb-4">Compare runs</h1>

      {/* Run picker */}
      <div className="flex flex-wrap items-end gap-3 mb-6">
        <RunSelect label="Run A" value={selA} runs={runs} onChange={setSelA} />
        <span className="text-slate-500 pb-2">vs</span>
        <RunSelect label="Run B" value={selB} runs={runs} onChange={setSelB} />
        <button
          onClick={compare}
          disabled={!selA || !selB || selA === selB}
          className="px-3 py-2 rounded-lg text-sm bg-indigo-500/20 border border-indigo-500/40 text-indigo-200 hover:bg-indigo-500/30 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Compare
        </button>
      </div>

      {error && <p className="text-rose-400 text-sm mb-3">Could not load runs: {error}</p>}

      {!left || !right ? (
        <p className="text-slate-500 text-sm">
          Pick two runs above to see a side-by-side diff of their metrics and loop warnings.
        </p>
      ) : (
        <div className="space-y-6">
          {/* Metrics table */}
          <div className="overflow-x-auto border border-edge rounded-lg bg-panel/40">
            <table className="w-full text-sm">
              <thead className="text-slate-400 text-xs uppercase tracking-wide">
                <tr className="border-b border-edge">
                  <th className="text-left font-medium px-4 py-3">Metric</th>
                  <th className="text-right font-medium px-4 py-3">
                    {left.run.name || left.run.id}
                  </th>
                  <th className="text-right font-medium px-4 py-3">Δ</th>
                  <th className="text-right font-medium px-4 py-3">
                    {right.run.name || right.run.id}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-edge/60">
                  <td className="px-4 py-3 text-slate-400">Health</td>
                  <td className="px-4 py-3 text-right">
                    <HealthBadge m={left.metrics} />
                  </td>
                  <td className="px-4 py-3" />
                  <td className="px-4 py-3 text-right">
                    <HealthBadge m={right.metrics} />
                  </td>
                </tr>
                {ROWS.map((row) => {
                  const av = row.pick(left.metrics);
                  const bv = row.pick(right.metrics);
                  return (
                    <tr key={row.label} className="border-b border-edge/60 hover:bg-edge/30">
                      <td className="px-4 py-3 text-slate-400">{row.label}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-200">
                        {row.fmt(av)}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums">
                        <Delta a={av} b={bv} fmt={row.fmt} higherBetter={row.higherBetter} />
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-slate-200">
                        {row.fmt(bv)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Warnings diff */}
          <div>
            <h2 className="text-sm font-semibold text-slate-300 mb-2">Loop warnings</h2>
            {warningTypes.length === 0 ? (
              <p className="text-slate-500 text-sm">Neither run raised a warning.</p>
            ) : (
              <div className="overflow-x-auto border border-edge rounded-lg bg-panel/40">
                <table className="w-full text-sm">
                  <thead className="text-slate-400 text-xs uppercase tracking-wide">
                    <tr className="border-b border-edge">
                      <th className="text-left font-medium px-4 py-3">Warning</th>
                      <th className="text-center font-medium px-4 py-3">A</th>
                      <th className="text-center font-medium px-4 py-3">B</th>
                    </tr>
                  </thead>
                  <tbody>
                    {warningTypes.map((t) => {
                      const inA = aTypes.has(t);
                      const inB = bTypes.has(t);
                      const differs = inA !== inB;
                      return (
                        <tr
                          key={t}
                          className={`border-b border-edge/60 ${differs ? "bg-amber-500/5" : ""}`}
                        >
                          <td className="px-4 py-3 text-slate-200">{warningTitle(t)}</td>
                          <Cell on={inA} />
                          <Cell on={inB} />
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Cell({ on }: { on: boolean }) {
  return (
    <td className="px-4 py-3 text-center">
      {on ? <span className="text-amber-300">●</span> : <span className="text-slate-600">—</span>}
    </td>
  );
}

function RunSelect({
  label,
  value,
  runs,
  onChange,
}: {
  label: string;
  value: string;
  runs: RunSummary[];
  onChange: (v: string) => void;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[11px] uppercase tracking-wide text-slate-500">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-panel border border-edge rounded-lg px-3 py-2 text-sm text-slate-200 min-w-[200px]"
      >
        <option value="">Select a run…</option>
        {runs.map((r) => (
          <option key={r.id} value={r.id}>
            {r.name || r.id}
          </option>
        ))}
      </select>
    </label>
  );
}
