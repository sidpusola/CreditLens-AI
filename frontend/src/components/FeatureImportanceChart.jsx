import { prettyFeature } from "../utils/format";

// Ranks all explanation factors by absolute SHAP impact (local importance).
export default function FeatureImportanceChart({ riskFactors = [], protectiveFactors = [] }) {
  const factors = [...riskFactors, ...protectiveFactors]
    .map((f) => ({ ...f, abs: Math.abs(f.impact) }))
    .sort((a, b) => b.abs - a.abs);

  if (factors.length === 0) return null;
  const max = factors[0].abs || 1;

  return (
    <div className="card p-5">
      <h3 className="mb-1 text-sm font-semibold text-white">Local Feature Importance</h3>
      <p className="mb-4 text-xs text-slate-500">Ranked by absolute SHAP impact for this applicant.</p>

      <div className="space-y-2.5">
        {factors.map((f, i) => {
          const isRisk = f.impact >= 0;
          return (
            <div key={i} className="flex items-center gap-3">
              <span className="w-40 shrink-0 truncate text-right text-xs text-slate-300" title={prettyFeature(f.feature)}>
                {prettyFeature(f.feature)}
              </span>
              <div className="h-4 flex-1 overflow-hidden rounded bg-ink-700/50">
                <div
                  className={`h-full rounded ${isRisk ? "bg-rose-500/80" : "bg-emerald-500/80"}`}
                  style={{ width: `${(f.abs / max) * 100}%` }}
                />
              </div>
              <span className="w-12 shrink-0 text-right text-xs font-semibold text-slate-300">
                {f.abs.toFixed(2)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
