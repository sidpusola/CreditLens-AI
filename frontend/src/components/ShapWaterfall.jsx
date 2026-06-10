import { prettyFeature } from "../utils/format";

// SHAP-style waterfall: factors sorted by signed impact, each bar floats at the
// running cumulative log-odds contribution. Risk factors push right (red),
// protective factors push left (green).
export default function ShapWaterfall({ riskFactors = [], protectiveFactors = [] }) {
  const factors = [...riskFactors, ...protectiveFactors].sort((a, b) => b.impact - a.impact);
  if (factors.length === 0) return null;

  // Build cumulative steps
  let running = 0;
  const steps = factors.map((f) => {
    const start = running;
    running += f.impact;
    return { ...f, start, end: running };
  });

  const totals = steps.flatMap((s) => [s.start, s.end]).concat(0);
  const min = Math.min(...totals);
  const max = Math.max(...totals);
  const span = max - min || 1;

  const W = 100; // percentage-based layout
  const toPct = (v) => ((v - min) / span) * W;
  const zeroPct = toPct(0);

  return (
    <div className="card p-5">
      <h3 className="mb-1 text-sm font-semibold text-white">SHAP Waterfall</h3>
      <p className="mb-4 text-xs text-slate-500">
        Cumulative contribution to the log-odds of default (left = protective, right = risk).
      </p>

      <div className="space-y-2">
        {steps.map((s, i) => {
          const isRisk = s.impact >= 0;
          const left = toPct(Math.min(s.start, s.end));
          const width = Math.max(0.8, Math.abs(toPct(s.end) - toPct(s.start)));
          return (
            <div key={i} className="flex items-center gap-3">
              <span className="w-40 shrink-0 truncate text-right text-xs text-slate-300" title={prettyFeature(s.feature)}>
                {prettyFeature(s.feature)}
              </span>
              <div className="relative h-5 flex-1 rounded bg-ink-700/40">
                {/* zero baseline */}
                <div className="absolute top-0 h-full w-px bg-slate-600" style={{ left: `${zeroPct}%` }} />
                {/* contribution segment */}
                <div
                  className={`absolute top-0.5 h-4 rounded ${isRisk ? "bg-rose-500/80" : "bg-emerald-500/80"}`}
                  style={{ left: `${left}%`, width: `${width}%` }}
                  title={`${s.impact > 0 ? "+" : ""}${s.impact.toFixed(3)}`}
                />
              </div>
              <span className={`w-14 shrink-0 text-right text-xs font-semibold ${isRisk ? "text-rose-400" : "text-emerald-400"}`}>
                {s.impact > 0 ? "+" : ""}
                {s.impact.toFixed(2)}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-ink-700 pt-3 text-xs">
        <span className="text-slate-400">Net contribution (shown factors)</span>
        <span className={`font-bold ${running >= 0 ? "text-rose-400" : "text-emerald-400"}`}>
          {running > 0 ? "+" : ""}
          {running.toFixed(3)}
        </span>
      </div>
    </div>
  );
}
