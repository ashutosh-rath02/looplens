import { WarningOut } from "../api";
import { severityClasses } from "../lib";

const TITLES: Record<string, string> = {
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

export default function WarningCard({ w }: { w: WarningOut }) {
  return (
    <div className={`border rounded-lg px-3 py-2.5 ${severityClasses(w.severity)}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-sm">{TITLES[w.type] ?? w.type}</span>
        <span className="text-[10px] uppercase tracking-wide opacity-70">{w.severity}</span>
      </div>
      <p className="text-xs mt-1 leading-relaxed opacity-90">{w.message}</p>
    </div>
  );
}
