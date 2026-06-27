import { EventOut } from "../api";
import { fmtTime } from "../lib";

function Section({ title, value }: { title: string; value: unknown }) {
  if (value == null) return null;
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-slate-500 mb-1">{title}</div>
      <pre className="text-xs bg-ink border border-edge rounded p-2 overflow-x-auto text-slate-300">
        {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}

export default function EventDrawer({ event, onClose }: { event: EventOut | null; onClose: () => void }) {
  if (!event) return null;
  return (
    <aside className="fixed inset-y-0 right-0 w-full max-w-md bg-panel border-l border-edge shadow-2xl z-20 flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-edge">
        <div>
          <div className="font-semibold text-slate-100">{event.type}</div>
          <div className="text-xs text-slate-500">
            #{event.sequence} · {fmtTime(event.timestamp)}
          </div>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white px-2 text-lg">
          ✕
        </button>
      </div>
      <div className="p-4 space-y-3 overflow-y-auto">
        <div className="grid grid-cols-2 gap-2 text-xs">
          {event.agent && <Meta k="agent" v={event.agent} />}
          {event.model && <Meta k="model" v={event.model} />}
          {event.tool && <Meta k="tool" v={event.tool} />}
          {event.status && <Meta k="status" v={event.status} />}
          {event.tokens != null && <Meta k="tokens" v={String(event.tokens)} />}
          {event.cost != null && <Meta k="cost" v={`$${event.cost}`} />}
          {event.latency_ms != null && <Meta k="latency" v={`${event.latency_ms}ms`} />}
        </div>
        <Section title="Input" value={event.input} />
        <Section title="Output" value={event.output} />
        <Section title="Error" value={event.error} />
        <Section title="Metadata" value={event.metadata} />
        <Section title="Raw" value={event} />
      </div>
    </aside>
  );
}

function Meta({ k, v }: { k: string; v: string }) {
  return (
    <div className="bg-ink border border-edge rounded px-2 py-1">
      <span className="text-slate-500">{k}: </span>
      <span className="text-slate-200">{v}</span>
    </div>
  );
}
