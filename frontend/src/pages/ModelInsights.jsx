import { useEffect, useState } from "react";
import { getModelInfo, getHealth } from "../api/client";
import MetricCard from "../components/MetricCard";
import StatusPill from "../components/StatusPill";

export default function ModelInsights() {
  const [info, setInfo] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getModelInfo(), getHealth()])
      .then(([i, h]) => {
        setInfo(i);
        setHealth(h);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Model Insights</h1>
          <p className="text-sm text-slate-400">Production model metadata</p>
        </div>
        <StatusPill ok={health?.model_loaded} loading={loading} labelOk="Model Loaded" labelBad="Not Loaded" />
      </div>

      {error && (
        <div className="card mb-6 border-rose-500/30 bg-rose-500/5 p-4 text-sm text-rose-300">{error}</div>
      )}

      {info && (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <MetricCard label="Algorithm" value={info.model_name} accent="text-accent-soft" />
            <MetricCard label="ROC-AUC" value={info.roc_auc.toFixed(4)} sub="Held-out test set" />
            <MetricCard label="Features" value={info.feature_count} sub="After one-hot encoding" />
            <MetricCard label="Version" value={info.model_version} sub={`Trained ${info.training_date}`} />
          </div>

          <div className="card mt-6 p-6">
            <h3 className="mb-4 text-sm font-semibold text-white">Feature Sources ({info.feature_sources.length})</h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {info.feature_sources.map((s) => (
                <div key={s} className="flex items-center gap-3 rounded-xl border border-ink-600 bg-ink-700 p-3">
                  <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent/15 text-xs font-bold text-accent-soft">
                    {s.slice(0, 2).toUpperCase()}
                  </span>
                  <span className="text-sm text-slate-200">{s}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card mt-6 p-6">
            <h3 className="mb-3 text-sm font-semibold text-white">How scores are categorized</h3>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
                <p className="text-sm font-semibold text-emerald-400">Low Risk</p>
                <p className="mt-1 text-xs text-slate-400">Risk score &lt; 40</p>
              </div>
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
                <p className="text-sm font-semibold text-amber-400">Medium Risk</p>
                <p className="mt-1 text-xs text-slate-400">40 ≤ score &lt; 70</p>
              </div>
              <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4">
                <p className="text-sm font-semibold text-rose-400">High Risk</p>
                <p className="mt-1 text-xs text-slate-400">Risk score ≥ 70</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
