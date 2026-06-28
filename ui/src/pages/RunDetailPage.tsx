import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { EventOut, Metrics, RunOut, WarningOut, getRun, streamRun } from "../api";
import { fmtTime, healthClasses } from "../lib";
import MetricsBar from "../components/MetricsBar";
import Timeline from "../components/Timeline";
import WarningCard from "../components/WarningCard";
import EventDrawer from "../components/EventDrawer";
import Diagnosis from "../components/Diagnosis";

export default function RunDetailPage() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<RunOut | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [warnings, setWarnings] = useState<WarningOut[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [selected, setSelected] = useState<EventOut | null>(null);
  const eventsRef = useRef<Map<number, EventOut>>(new Map());
  const [, force] = useState(0);

  useEffect(() => {
    if (!runId) return;
    eventsRef.current = new Map();
    getRun(runId).then(setRun).catch(() => {});
    const stop = streamRun(runId, (u) => {
      for (const e of u.events) eventsRef.current.set(e.sequence, e);
      setMetrics(u.metrics);
      setWarnings(u.warnings);
      setStatus(u.status);
      force((n) => n + 1);
    });
    return stop;
  }, [runId]);

  const events = useMemo(
    () => [...eventsRef.current.values()].sort((a, b) => a.sequence - b.sequence),
    [eventsRef.current.size, metrics] // eslint-disable-line react-hooks/exhaustive-deps
  );
  const warnEventIds = useMemo(
    () => new Set(warnings.map((w) => w.event_id).filter(Boolean) as string[]),
    [warnings]
  );
  const eventsById = useMemo(
    () => new Map(events.map((e) => [e.event_id, e])),
    [events]
  );
  const jumpToEvent = (eventId: string) => {
    const e = eventsById.get(eventId);
    if (e) setSelected(e); // highlights + scrolls the timeline, opens the drawer
  };
  const health = status === "failed" ? "Failed" : metrics?.loop_health_status;

  return (
    <div>
      <div className="flex items-center gap-2 mb-4 text-sm">
        <Link to="/" className="text-slate-400 hover:text-white">
          ← Runs
        </Link>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">{run?.name || runId}</h1>
          <div className="text-xs text-slate-500">
            {status || run?.status} · started {fmtTime(run?.started_at)}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {metrics && (
            <span className="text-xs text-slate-500">
              health <span className="text-slate-300 tabular-nums">{metrics.health_score}</span>/100
            </span>
          )}
          <span className={`text-sm px-3 py-1 rounded-full border ${healthClasses(health)}`}>
            {health || "—"}
          </span>
        </div>
      </div>

      <div className="mb-4">
        <Diagnosis warnings={warnings} metrics={metrics} status={status} />
      </div>

      <div className="mb-5">
        <MetricsBar m={metrics} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <section className="lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-300 mb-2">Timeline</h2>
          <div className="border border-edge rounded-lg bg-panel/40 max-h-[60vh] overflow-y-auto">
            <Timeline
              events={events}
              warnEventIds={warnEventIds}
              selectedId={selected?.event_id ?? null}
              onSelect={setSelected}
            />
          </div>
        </section>

        <section>
          <h2 className="text-sm font-semibold text-slate-300 mb-2">
            Warnings {warnings.length > 0 && <span className="text-amber-300">({warnings.length})</span>}
          </h2>
          {warnings.length === 0 ? (
            <div className="border border-edge rounded-lg p-6 text-center text-slate-500 text-sm bg-panel/40">
              No loop warnings. 🎉
            </div>
          ) : (
            <div className="space-y-2">
              {warnings.map((w) => (
                <WarningCard
                  key={w.warning_id}
                  w={w}
                  onJump={w.event_id ? () => jumpToEvent(w.event_id!) : undefined}
                />
              ))}
            </div>
          )}
        </section>
      </div>

      <EventDrawer event={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
