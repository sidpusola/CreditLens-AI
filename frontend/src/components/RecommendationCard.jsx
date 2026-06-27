import { decisionFor, confidenceScore } from "../utils/report";
import { prettyFeature, isSoftFactor } from "../utils/format";

const TONE = {
  rose: { text: "text-rose-400", bg: "bg-rose-500/10", border: "border-rose-500/30", dot: "bg-rose-400", icon: "M6 18L18 6M6 6l12 12" },
  amber: { text: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30", dot: "bg-amber-400", icon: "M12 9v4m0 4h.01M10.3 3.9l-8 14A2 2 0 004 21h16a2 2 0 001.7-3.1l-8-14a2 2 0 00-3.4 0z" },
  emerald: { text: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30", dot: "bg-emerald-400", icon: "M5 13l4 4L19 7" },
};

function reasonFor(category) {
  if (category === "High Risk") return "Default probability exceeds the high-risk threshold.";
  if (category === "Medium Risk") return "Moderate default probability — manual review advised before approval.";
  return "Default probability is within acceptable limits.";
}

export default function RecommendationCard({ prediction, explanation }) {
  const decision = decisionFor(prediction.risk_category);
  const tone = TONE[decision.tone];
  const confidence = confidenceScore(prediction.default_probability);
  const drivers = explanation.top_risk_factors.filter((f) => !isSoftFactor(f.feature)).slice(0, 3);
  const mitigants = explanation.top_protective_factors.slice(0, 3);

  return (
    <div className={`card border ${tone.border} p-6`}>
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">Recommendation</h3>

      {/* Decision + confidence */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className={`grid h-9 w-9 place-items-center rounded-xl ${tone.bg} ${tone.text}`}>
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.2">
              <path strokeLinecap="round" strokeLinejoin="round" d={tone.icon} />
            </svg>
          </span>
          <div>
            <p className="text-[11px] uppercase tracking-wide text-slate-500">Decision</p>
            <p className={`text-lg font-bold ${tone.text}`}>{decision.verdict}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Confidence</p>
          <p className="text-lg font-bold text-accent-soft">{confidence}%</p>
        </div>
      </div>

      {/* Reason */}
      <div className="mt-4 rounded-xl border border-ink-600 bg-ink-900/40 p-3">
        <p className="text-[11px] uppercase tracking-wide text-slate-500">Reason</p>
        <p className="mt-0.5 text-sm text-slate-200">{reasonFor(prediction.risk_category)}</p>
      </div>

      {/* Key drivers + mitigants */}
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-2 flex items-center gap-2 text-xs font-semibold text-rose-400">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-400" /> Key Drivers
          </p>
          <ul className="space-y-1.5">
            {drivers.length ? (
              drivers.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-rose-400/70" />
                  {prettyFeature(f.feature)}
                </li>
              ))
            ) : (
              <li className="text-sm text-slate-500">None material</li>
            )}
          </ul>
        </div>
        <div>
          <p className="mb-2 flex items-center gap-2 text-xs font-semibold text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Mitigating Factors
          </p>
          <ul className="space-y-1.5">
            {mitigants.length ? (
              mitigants.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-emerald-400/70" />
                  {prettyFeature(f.feature)}
                </li>
              ))
            ) : (
              <li className="text-sm text-slate-500">None</li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
