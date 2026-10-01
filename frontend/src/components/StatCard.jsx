import { cn } from "../utils/cn.js";

/** Single KPI. `value` of null/undefined renders an em dash (no data yet). */
export default function StatCard({ label, value, unit, hint, className }) {
  const hasValue = value !== null && value !== undefined && value !== "";
  return (
    <div className={cn("rounded-xl border border-slate-200 bg-white p-5 shadow-sm", className)}>
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-2 flex items-baseline gap-1.5">
        <span className="text-2xl font-semibold text-slate-900">{hasValue ? value : "—"}</span>
        {unit && <span className="text-sm text-slate-500">{unit}</span>}
      </p>
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}
