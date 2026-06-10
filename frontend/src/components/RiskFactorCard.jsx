import { prettyFeature } from "../utils/format";

// A single SHAP factor row. `kind` is "risk" (positive impact) or "protective" (negative).
export default function RiskFactorCard({ factor, kind }) {
  const isRisk = kind === "risk";
  const color = isRisk ? "text-rose-400" : "text-emerald-400";
  const barColor = isRisk ? "bg-rose-500" : "bg-emerald-500";
  const magnitude = Math.min(100, Math.abs(factor.impact) * 100);

  return (
    <div className="card flex items-center gap-4 p-4">
      <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-ink-700 ${color}`}>
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.2">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d={isRisk ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"}
          />
        </svg>
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-slate-100">{prettyFeature(factor.feature)}</p>
        <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-ink-700">
          <div className={`h-full rounded-full ${barColor}`} style={{ width: `${magnitude}%` }} />
        </div>
      </div>
      <span className={`shrink-0 text-sm font-bold ${color}`}>
        {factor.impact > 0 ? "+" : ""}
        {factor.impact.toFixed(3)}
      </span>
    </div>
  );
}
