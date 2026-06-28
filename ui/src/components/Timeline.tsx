import { useEffect, useRef } from "react";
import { EventOut } from "../api";
import { eventColor } from "../lib";

interface Props {
  events: EventOut[];
  warnEventIds: Set<string>;
  selectedId: string | null;
  onSelect: (e: EventOut) => void;
}

export default function Timeline({ events, warnEventIds, selectedId, onSelect }: Props) {
  const selectedRef = useRef<HTMLButtonElement>(null);
  // Bring the selected row into view — e.g. after jumping from a warning.
  useEffect(() => {
    selectedRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [selectedId]);

  if (events.length === 0) {
    return <div className="text-slate-500 text-sm py-8 text-center">Waiting for events…</div>;
  }
  return (
    <div className="divide-y divide-edge/60">
      {events.map((e) => {
        const label = e.tool || e.model || e.name || e.agent || "";
        const flagged = warnEventIds.has(e.event_id);
        return (
          <button
            key={e.event_id}
            ref={selectedId === e.event_id ? selectedRef : undefined}
            onClick={() => onSelect(e)}
            className={`w-full text-left flex items-center gap-3 px-3 py-2 hover:bg-edge/30 ${
              selectedId === e.event_id ? "bg-edge/50" : ""
            }`}
          >
            <span className="text-[11px] text-slate-600 tabular-nums w-7 shrink-0">{e.sequence}</span>
            <span className={`text-sm font-medium shrink-0 ${eventColor(e.type)}`}>{e.type}</span>
            {label && <span className="text-xs text-slate-400 truncate">{label}</span>}
            <span className="ml-auto flex items-center gap-2 shrink-0">
              {flagged && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  loop
                </span>
              )}
              {e.latency_ms != null && (
                <span className="text-[11px] text-slate-500 tabular-nums">{e.latency_ms}ms</span>
              )}
            </span>
          </button>
        );
      })}
    </div>
  );
}
