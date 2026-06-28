// REST + SSE client for the LoopLens backend.

export interface RunSummary {
  id: string;
  name: string | null;
  project: string | null;
  status: string | null;
  started_at: string | null;
  ended_at: string | null;
  total_cost: number;
  total_tokens: number;
  event_count: number;
  warning_count: number;
  health_score: number;
  loop_health_status: string;
}

export interface RunOut extends RunSummary {
  metadata?: Record<string, unknown> | null;
}

export interface EventOut {
  event_id: string;
  run_id: string;
  sequence: number;
  timestamp: string;
  type: string;
  agent?: string | null;
  name?: string | null;
  status?: string | null;
  model?: string | null;
  tool?: string | null;
  input?: unknown;
  output?: unknown;
  error?: unknown;
  tokens?: number | null;
  cost?: number | null;
  latency_ms?: number | null;
  metadata?: Record<string, unknown> | null;
}

export interface WarningOut {
  warning_id: string;
  run_id: string;
  event_id?: string | null;
  type: string;
  severity: "info" | "warning" | "critical";
  message: string;
  details?: Record<string, unknown> | null;
  created_at: string;
}

export interface Metrics {
  run_id: string;
  total_events: number;
  total_duration_sec: number;
  total_llm_calls: number;
  total_tool_calls: number;
  total_retries: number;
  total_handoffs: number;
  total_errors: number;
  total_tokens: number;
  estimated_cost: number;
  average_latency_ms: number;
  max_latency_ms: number;
  most_used_tool: string | null;
  most_active_agent: string | null;
  warnings_count: number;
  health_score: number;
  loop_health_status: string;
}

export interface StreamUpdate {
  type: "update";
  events: EventOut[];
  metrics: Metrics;
  warnings: WarningOut[];
  status: string | null;
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const listRuns = () => getJSON<RunSummary[]>("/api/runs");
export const getRun = (id: string) => getJSON<RunOut>(`/api/runs/${id}`);
export const getEvents = (id: string) => getJSON<EventOut[]>(`/api/runs/${id}/events`);
export const getWarnings = (id: string) => getJSON<WarningOut[]>(`/api/runs/${id}/warnings`);
export const getMetrics = (id: string) => getJSON<Metrics>(`/api/runs/${id}/metrics`);

export function streamRun(id: string, onUpdate: (u: StreamUpdate) => void): () => void {
  const es = new EventSource(`/api/runs/${id}/stream`);
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data?.type === "update") onUpdate(data as StreamUpdate);
    } catch {
      /* ignore keepalive / malformed frames */
    }
  };
  return () => es.close();
}
