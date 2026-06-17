import { useState } from "react";
import { postReport } from "../api/client";

// LLM-generated underwriting narrative (RAG: grounded in score + SHAP + similar cases).
export default function UnderwritingReport({ features }) {
  const [report, setReport] = useState(null);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await postReport(features, 5);
      setReport(data.report);
      setMeta({ model: data.model, similar: data.similar_used });
    } catch (err) {
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-6">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">AI Underwriting Report</h3>
          <p className="text-xs text-slate-500">
            Generated locally by an LLM, grounded in the risk score, SHAP factors, and similar cases (RAG).
          </p>
        </div>
        <button onClick={generate} disabled={loading} className="btn-primary no-print">
          {loading ? "Generating…" : report ? "Regenerate" : "Generate Report"}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/5 p-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      {loading && !report && (
        <p className="text-sm text-slate-500">Writing the report… this can take a few seconds on local hardware.</p>
      )}

      {report && (
        <>
          <div className="whitespace-pre-wrap rounded-xl border border-ink-600 bg-ink-900/40 p-4 text-sm leading-relaxed text-slate-200">
            {report}
          </div>
          {meta && (
            <p className="mt-2 text-[11px] text-slate-600">
              Model: {meta.model} · grounded on {meta.similar} similar case{meta.similar === 1 ? "" : "s"}
            </p>
          )}
        </>
      )}
    </div>
  );
}
