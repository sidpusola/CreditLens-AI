import { useState } from "react";
import { postReport } from "../api/client";

// Render the LLM's lightweight markdown (## headings, **bold**, - bullets) as a styled memo.
function renderMemo(text) {
  const blocks = [];
  let list = [];
  const flush = (key) => {
    if (list.length) {
      blocks.push(
        <ul key={`ul-${key}`} className="ml-1 list-disc space-y-1 pl-4 text-slate-300 marker:text-slate-600">
          {list.map((it, i) => (
            <li key={i}>{inline(it)}</li>
          ))}
        </ul>
      );
      list = [];
    }
  };
  const inline = (s) =>
    s.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
      part.startsWith("**") && part.endsWith("**") ? (
        <strong key={i} className="font-semibold text-white">{part.slice(2, -2)}</strong>
      ) : (
        <span key={i}>{part}</span>
      )
    );

  text.split("\n").forEach((raw, idx) => {
    const line = raw.trim();
    if (!line) {
      flush(idx);
      return;
    }
    if (line.startsWith("## ")) {
      flush(idx);
      blocks.push(
        <h4 key={`h-${idx}`} className="mt-4 flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-accent-soft first:mt-0">
          <span className="h-1 w-4 rounded-full bg-accent" /> {line.slice(3)}
        </h4>
      );
    } else if (line.startsWith("- ") || line.startsWith("* ")) {
      list.push(line.slice(2));
    } else {
      flush(idx);
      blocks.push(<p key={`p-${idx}`} className="text-sm leading-relaxed text-slate-300">{inline(line)}</p>);
    }
  });
  flush("end");
  return blocks;
}

// LLM-generated underwriting memo (RAG: grounded in score + SHAP + similar cases + case file).
export default function UnderwritingReport({ features, caseMeta }) {
  const [report, setReport] = useState(null);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await postReport(features, caseMeta || null, 5);
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
          <h3 className="text-sm font-semibold text-white">AI Underwriting Memo</h3>
          <p className="text-xs text-slate-500">
            Drafted locally by an LLM — grounded in the risk score, evidence, and comparable cases (RAG).
          </p>
        </div>
        <button onClick={generate} disabled={loading} className="btn-primary no-print">
          {loading ? "Drafting…" : report ? "Regenerate" : "Generate Memo"}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/5 p-3 text-sm text-rose-300">{error}</div>
      )}

      {loading && !report && (
        <p className="text-sm text-slate-500">Drafting the memo… this can take a few seconds on local hardware.</p>
      )}

      {report && (
        <>
          <div className="space-y-2 rounded-xl border border-ink-600 bg-ink-900/40 p-5">{renderMemo(report)}</div>
          {meta && (
            <p className="mt-2 text-[11px] text-slate-600">
              {meta.model} · grounded on {meta.similar} comparable case{meta.similar === 1 ? "" : "s"}
            </p>
          )}
        </>
      )}
    </div>
  );
}
