import { Metrics, WarningOut } from "../api";
import { diagnose } from "../lib";

const TONE: Record<string, string> = {
  good: "bg-emerald-500/10 border-emerald-500/30 text-emerald-200",
  warn: "bg-amber-500/10 border-amber-500/30 text-amber-200",
  bad: "bg-rose-500/10 border-rose-500/30 text-rose-200",
};

const ICON: Record<string, string> = { good: "✓", warn: "▲", bad: "■" };

export default function Diagnosis({
  warnings,
  metrics,
  status,
}: {
  warnings: WarningOut[];
  metrics: Metrics | null;
  status: string | null;
}) {
  const d = diagnose(warnings, metrics, status);
  if (!d) return null;
  return (
    <div className={`rounded-lg border px-4 py-2.5 flex items-center gap-2.5 ${TONE[d.tone]}`}>
      <span className="text-xs">{ICON[d.tone]}</span>
      <span className="text-sm font-medium">{d.text}</span>
    </div>
  );
}
