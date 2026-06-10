import { decisionFor } from "../utils/report";
import { prettyFeature } from "../utils/format";

const TONE = {
  rose: { text: "text-rose-400", bg: "bg-rose-500/10", border: "border-rose-500/30", dot: "bg-rose-400" },
  amber: { text: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30", dot: "bg-amber-400" },
  emerald: { text: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30", dot: "bg-emerald-400" },
};

export default function DecisionSummary({ prediction, explanation }) {
  const decision = decisionFor(prediction.risk_category);
  const tone = TONE[decision.tone];
  const topRisk = explanation.top_risk_factors[0];
  const topProtective = explanation.top_protective_factors[0];

  return (
    <div className={`card border ${tone.border} p-6`}>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Decision Summary</h3>
        <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${tone.bg} ${tone.text}`}>
          <span className={`h-2 w-2 rounded-full ${tone.dot}`} /> {decision.verdict}
        </span>
      </div>

      <p className="text-sm leading-relaxed text-slate-300">{decision.blurb}</p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-ink-600 bg-ink-700/50 p-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Primary risk driver</p>
          {topRisk ? (
            <p className="mt-1 text-sm font-semibold text-rose-400">
              {prettyFeature(topRisk.feature)} <span className="text-slate-500">(+{topRisk.impact.toFixed(2)})</span>
            </p>
          ) : (
            <p className="mt-1 text-sm text-slate-500">None</p>
          )}
        </div>
        <div className="rounded-xl border border-ink-600 bg-ink-700/50 p-3">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Primary mitigant</p>
          {topProtective ? (
            <p className="mt-1 text-sm font-semibold text-emerald-400">
              {prettyFeature(topProtective.feature)} <span className="text-slate-500">({topProtective.impact.toFixed(2)})</span>
            </p>
          ) : (
            <p className="mt-1 text-sm text-slate-500">None</p>
          )}
        </div>
      </div>
    </div>
  );
}
