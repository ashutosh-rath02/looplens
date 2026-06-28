import { WarningOut } from "../api";
import { severityClasses, warningTitle } from "../lib";

export default function WarningCard({ w }: { w: WarningOut }) {
  return (
    <div className={`border rounded-lg px-3 py-2.5 ${severityClasses(w.severity)}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-sm">{warningTitle(w.type)}</span>
        <span className="text-[10px] uppercase tracking-wide opacity-70">{w.severity}</span>
      </div>
      <p className="text-xs mt-1 leading-relaxed opacity-90">{w.message}</p>
    </div>
  );
}
