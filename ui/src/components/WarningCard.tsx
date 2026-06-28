import { WarningOut } from "../api";
import { severityClasses, warningTitle } from "../lib";

export default function WarningCard({ w, onJump }: { w: WarningOut; onJump?: () => void }) {
  const clickable = !!onJump;
  return (
    <div
      onClick={onJump}
      role={clickable ? "button" : undefined}
      className={`border rounded-lg px-3 py-2.5 ${severityClasses(w.severity)} ${
        clickable ? "cursor-pointer hover:brightness-125 transition" : ""
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-sm">{warningTitle(w.type)}</span>
        <span className="text-[10px] uppercase tracking-wide opacity-70">{w.severity}</span>
      </div>
      <p className="text-xs mt-1 leading-relaxed opacity-90">{w.message}</p>
      {clickable && <p className="text-[10px] mt-1.5 opacity-60">→ jump to the event</p>}
    </div>
  );
}
