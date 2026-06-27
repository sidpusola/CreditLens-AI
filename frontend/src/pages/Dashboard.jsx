import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getHealth, getModelInfo } from "../api/client";
import StatusPill from "../components/StatusPill";
import DecisionBadge from "../components/DecisionBadge";
import { useAssessment } from "../context/AssessmentContext";
import { riskTheme } from "../utils/format";

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

const ICONS = {
  auc: "M3 17l6-6 4 4 8-8M21 7h-4M21 7v4",
  features: "M4 6h16M4 12h16M4 18h10",
  sources: "M4 7h16M4 7a2 2 0 002 2h12a2 2 0 002-2M4 7a2 2 0 012-2h12a2 2 0 012 2M8 11v6m4-6v6m4-6v6",
  model: "M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 7h10v10H7z",
};

function Kpi({ label, value, sub, icon, glow }) {
  return (
    <div className="card relative overflow-hidden p-5">
      <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${glow}`} />
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
          <p className="mt-2 text-3xl font-bold text-white">{value}</p>
          {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
        </div>
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-ink-700 text-accent-soft">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
            <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
          </svg>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const { history, selectAssessment } = useAssessment();
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([getHealth(), getModelInfo()])
      .then(([h, i]) => {
        setHealth(h);
        setInfo(i);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // Portfolio risk mix from saved assessments
  const mix = { "High Risk": 0, "Medium Risk": 0, "Low Risk": 0 };
  history.forEach((h) => {
    mix[h.prediction.risk_category] = (mix[h.prediction.risk_category] || 0) + 1;
  });
  const total = history.length || 1;

  // Operational stats from the assessment history
  const todayStr = new Date().toDateString();
  const todays = history.filter((h) => new Date(h.submittedAt).toDateString() === todayStr).length;
  const avgRisk = history.length
    ? (history.reduce((s, h) => s + h.prediction.risk_score, 0) / history.length).toFixed(1)
    : "—";
  const approved = history.filter((h) => h.decision === "Approved").length;
  const rejected = history.filter((h) => h.decision === "Rejected").length;
  const pending = history.filter((h) => !h.decision || h.decision === "Manual Review").length;
  const decided = history.filter((h) => h.decided_at && h.submittedAt);
  const avgProcMs = decided.length
    ? decided.reduce((s, h) => s + (new Date(h.decided_at) - new Date(h.submittedAt)), 0) / decided.length
    : null;
  const avgProc =
    avgProcMs == null
      ? "—"
      : avgProcMs < 60000
      ? `${Math.round(avgProcMs / 1000)}s`
      : avgProcMs < 3600000
      ? `${Math.round(avgProcMs / 60000)}m`
      : `${(avgProcMs / 3600000).toFixed(1)}h`;

  const ops = [
    { label: "Today's Applications", value: todays, tone: "text-white" },
    { label: "Average Risk", value: avgRisk, tone: "text-accent-soft" },
    { label: "Approved", value: approved, tone: "text-emerald-400" },
    { label: "Pending Review", value: pending, tone: "text-amber-400" },
    { label: "Rejected", value: rejected, tone: "text-rose-400" },
    { label: "Avg Processing", value: avgProc, tone: "text-white" },
  ];

  const openReport = (id) => {
    selectAssessment(id);
    navigate("/report");
  };

  // Search across the case book by applicant/case id or name
  const q = query.trim().toLowerCase();
  const results = q
    ? history.filter(
        (h) =>
          (h.case?.applicant_id || "").toLowerCase().includes(q) ||
          (h.case?.applicant_name || "").toLowerCase().includes(q) ||
          h.id.toLowerCase().includes(q)
      )
    : [];

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl border border-ink-600/60 bg-gradient-to-br from-accent/25 via-ink-800 to-ink-800 p-7">
        <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-accent/20 blur-3xl" />
        <div className="relative flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-accent-soft">{greeting()}, Underwriter</p>
            <h1 className="mt-1 text-3xl font-extrabold text-white">Underwriting Command Center</h1>
            <p className="mt-1 max-w-xl text-sm text-slate-300">
              Score applicants, explain every decision with SHAP, surface comparable precedent, and
              generate AI underwriting reports — all in one place.
            </p>
            <div className="mt-4 flex gap-2">
              <Link to="/assess" className="btn-primary">New Assessment</Link>
              <Link
                to="/model"
                className="inline-flex items-center rounded-xl border border-ink-600 bg-ink-800/60 px-4 py-2.5 text-sm font-semibold text-slate-200 hover:bg-ink-700"
              >
                Model Insights
              </Link>
            </div>
          </div>
          <StatusPill ok={health?.model_loaded} loading={loading} labelOk="System Online" labelBad="API Offline" />
        </div>
      </div>

      {/* Search the case book */}
      <div className="relative">
        <div className="card flex items-center gap-3 px-4 py-3">
          <svg className="h-5 w-5 shrink-0 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.3-4.3m1.3-5.4a6.7 6.7 0 11-13.4 0 6.7 6.7 0 0113.4 0z" />
          </svg>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by Applicant ID, Case ID, or name…"
            className="w-full bg-transparent text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
          />
          {query && (
            <button onClick={() => setQuery("")} className="text-xs text-slate-500 hover:text-slate-300">Clear</button>
          )}
        </div>
        {q && (
          <div className="card absolute z-10 mt-2 max-h-72 w-full overflow-y-auto p-2">
            {results.length === 0 ? (
              <p className="px-3 py-4 text-center text-sm text-slate-500">No matches for “{query}”.</p>
            ) : (
              results.slice(0, 8).map((h) => {
                const theme = riskTheme(h.prediction.risk_category);
                return (
                  <button
                    key={h.id}
                    onClick={() => openReport(h.id)}
                    className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left hover:bg-ink-700"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-slate-100">
                        {h.case?.applicant_name || "Unnamed"}
                      </p>
                      <p className="truncate font-mono text-[11px] text-slate-500">{h.case?.applicant_id || h.id.slice(0, 8)}</p>
                    </div>
                    <span className={`shrink-0 text-sm font-bold ${theme.text}`}>{h.prediction.risk_score.toFixed(0)}</span>
                  </button>
                );
              })
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="card border-rose-500/30 bg-rose-500/5 p-4 text-sm text-rose-300">
          Could not reach the backend: {error}. Make sure the FastAPI server is running on port 8000.
        </div>
      )}

      {/* Operational stats */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-white">Today's Activity</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {ops.map((s) => (
            <div key={s.label} className="card p-4">
              <p className="text-[11px] uppercase tracking-wide text-slate-500">{s.label}</p>
              <p className={`mt-1.5 text-2xl font-bold ${s.tone}`}>{s.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Model KPI cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Kpi label="Model ROC-AUC" value={info ? info.roc_auc.toFixed(4) : "—"} sub="Primary metric" icon={ICONS.auc} glow="from-indigo-500 to-violet-500" />
        <Kpi label="Features" value={info?.feature_count ?? "—"} sub="After encoding" icon={ICONS.features} glow="from-sky-500 to-cyan-500" />
        <Kpi label="Data Sources" value={info?.feature_sources?.length ?? "—"} sub="Merged tables" icon={ICONS.sources} glow="from-emerald-500 to-teal-500" />
        <Kpi label="Assessments" value={history.length} sub="Saved to date" icon={ICONS.model} glow="from-amber-500 to-orange-500" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent assessments */}
        <div className="card p-6 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Recent Assessments</h3>
            <Link to="/assess" className="text-xs font-medium text-accent-soft hover:underline">+ New</Link>
          </div>

          {history.length === 0 ? (
            <div className="rounded-xl border border-dashed border-ink-600 p-8 text-center">
              <p className="text-sm text-slate-400">No assessments yet.</p>
              <Link to="/assess" className="btn-primary mt-4">Run your first assessment</Link>
            </div>
          ) : (
            <ul className="divide-y divide-ink-700/60">
              {history.slice(0, 6).map((h) => {
                const theme = riskTheme(h.prediction.risk_category);
                return (
                  <li key={h.id}>
                    <button
                      onClick={() => openReport(h.id)}
                      className="flex w-full items-center gap-4 py-3 text-left transition hover:opacity-80"
                    >
                      <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${theme.bg}`}>
                        <span className={`text-sm font-bold ${theme.text}`}>{h.prediction.risk_score.toFixed(0)}</span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                          <span className="truncate">{h.case?.applicant_name || h.prediction.risk_category}</span>
                          <DecisionBadge decision={h.decision} short />
                        </p>
                        <p className="truncate text-[11px] text-slate-500">
                          {h.prediction.risk_category} · {(h.prediction.default_probability * 100).toFixed(1)}% PD · {new Date(h.submittedAt).toLocaleDateString()}
                        </p>
                      </div>
                      <svg className="h-4 w-4 shrink-0 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        {/* Portfolio risk mix */}
        <div className="card p-6">
          <h3 className="mb-4 text-sm font-semibold text-white">Portfolio Risk Mix</h3>
          {history.length === 0 ? (
            <p className="text-sm text-slate-500">Run assessments to see your portfolio breakdown.</p>
          ) : (
            <>
              <div className="mb-4 flex h-3 overflow-hidden rounded-full bg-ink-700">
                <div className="bg-emerald-500" style={{ width: `${(mix["Low Risk"] / total) * 100}%` }} />
                <div className="bg-amber-500" style={{ width: `${(mix["Medium Risk"] / total) * 100}%` }} />
                <div className="bg-rose-500" style={{ width: `${(mix["High Risk"] / total) * 100}%` }} />
              </div>
              <ul className="space-y-2 text-sm">
                {[
                  ["Low Risk", "bg-emerald-400", "text-emerald-400"],
                  ["Medium Risk", "bg-amber-400", "text-amber-400"],
                  ["High Risk", "bg-rose-400", "text-rose-400"],
                ].map(([cat, dot, txt]) => (
                  <li key={cat} className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-slate-300">
                      <span className={`h-2 w-2 rounded-full ${dot}`} /> {cat}
                    </span>
                    <span className={`font-semibold ${txt}`}>{mix[cat]}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </div>

      {/* Feature sources */}
      {info && (
        <div className="card p-6">
          <h3 className="mb-3 text-sm font-semibold text-white">Data Sources Powering the Model</h3>
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
