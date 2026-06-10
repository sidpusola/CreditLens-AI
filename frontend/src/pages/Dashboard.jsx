import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHealth, getModelInfo } from "../api/client";
import MetricCard from "../components/MetricCard";
import StatusPill from "../components/StatusPill";

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getHealth(), getModelInfo()])
      .then(([h, i]) => {
        setHealth(h);
        setInfo(i);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-slate-400">Loan default risk intelligence overview</p>
        </div>
        <StatusPill ok={health?.model_loaded} loading={loading} labelOk="API Online" labelBad="API Offline" />
      </div>

      {error && (
        <div className="card mb-6 border-rose-500/30 bg-rose-500/5 p-4 text-sm text-rose-300">
          Could not reach the backend: {error}. Make sure the FastAPI server is running on port 8000.
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          label="Model ROC-AUC"
          value={info ? info.roc_auc.toFixed(4) : "—"}
          sub="Primary metric"
          accent="text-accent-soft"
        />
        <MetricCard label="Features" value={info?.feature_count ?? "—"} sub="After encoding" />
        <MetricCard label="Data Sources" value={info?.feature_sources?.length ?? "—"} sub="Merged tables" />
        <MetricCard label="Model" value={info?.model_name ?? "—"} sub={info?.training_date ?? ""} />
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <Link to="/assess" className="card group p-6 transition hover:border-accent/50">
          <div className="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-accent/15 text-accent-soft">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white">New Assessment</h3>
          <p className="mt-1 text-sm text-slate-400">
            Enter applicant details and get an instant default-risk score with SHAP explanation.
          </p>
        </Link>

        <Link to="/model" className="card group p-6 transition hover:border-accent/50">
          <div className="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-accent/15 text-accent-soft">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M11 3.05V11h7.95A8 8 0 1011 3.05z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white">Model Insights</h3>
          <p className="mt-1 text-sm text-slate-400">
            Inspect the production model: metrics, feature sources, and training metadata.
          </p>
        </Link>
      </div>

      {info && (
        <div className="card mt-6 p-6">
          <h3 className="mb-3 text-sm font-semibold text-white">Feature Sources</h3>
          <div className="flex flex-wrap gap-2">
            {info.feature_sources.map((s) => (
              <span key={s} className="rounded-lg border border-ink-600 bg-ink-700 px-3 py-1 text-xs text-slate-300">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
