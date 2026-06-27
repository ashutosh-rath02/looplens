import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listRuns, RunSummary } from "../api";
import { fmtCost, fmtTime, healthClasses } from "../lib";

export default function RunsPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () =>
      listRuns()
        .then((r) => alive && setRuns(r))
        .catch((e) => alive && setError(String(e)));
    load();
    const t = setInterval(load, 2000); // poll the runs list
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  return (
    <div>
      <div className="flex items-baseline justify-between mb-4">
        <h1 className="text-xl font-semibold text-slate-100">Runs</h1>
        <span className="text-xs text-slate-500">{runs.length} total · live</span>
      </div>

      {error && <p className="text-rose-400 text-sm mb-3">Could not reach the server: {error}</p>}

      {runs.length === 0 ? (
        <div className="border border-edge rounded-lg p-10 text-center text-slate-500 bg-panel/40">
          No runs yet. Run <code className="text-slate-300">looplens demo</code> or instrument your
          agent with the SDK.
        </div>
      ) : (
        <div className="overflow-x-auto border border-edge rounded-lg bg-panel/40">
          <table className="w-full text-sm">
            <thead className="text-slate-400 text-xs uppercase tracking-wide">
              <tr className="border-b border-edge">
                <th className="text-left font-medium px-4 py-3">Run</th>
                <th className="text-left font-medium px-4 py-3">Health</th>
                <th className="text-right font-medium px-4 py-3">Steps</th>
                <th className="text-right font-medium px-4 py-3">Warnings</th>
                <th className="text-right font-medium px-4 py-3">Tokens</th>
                <th className="text-right font-medium px-4 py-3">Cost</th>
                <th className="text-left font-medium px-4 py-3">Started</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id} className="border-b border-edge/60 hover:bg-edge/30">
                  <td className="px-4 py-3">
                    <Link to={`/runs/${r.id}`} className="text-slate-100 hover:text-white font-medium">
                      {r.name || r.id}
                    </Link>
                    <div className="text-xs text-slate-500">{r.status}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded border ${healthClasses(
                        r.status === "failed" ? "Failed" : undefined
                      )}`}
                    >
                      {r.status === "failed" ? "Failed" : r.status || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">{r.event_count}</td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {r.warning_count > 0 ? (
                      <span className="text-amber-300">{r.warning_count}</span>
                    ) : (
                      <span className="text-slate-500">0</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">{r.total_tokens}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{fmtCost(r.total_cost)}</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{fmtTime(r.started_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
