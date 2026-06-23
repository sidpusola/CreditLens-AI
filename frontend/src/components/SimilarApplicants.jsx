import { useEffect, useState } from "react";
import { postSimilar } from "../api/client";
import { riskTheme } from "../utils/format";

function OutcomeBadge({ outcome }) {
  if (!outcome) return null;
  const defaulted = /default/i.test(outcome);
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
        defaulted ? "bg-rose-500/15 text-rose-400" : "bg-emerald-500/15 text-emerald-400"
      }`}
    >
      {defaulted ? "Defaulted" : "Repaid"}
    </span>
  );
}

// pgvector nearest-neighbour precedents, enriched with outcome + the features that drove the match.
export default function SimilarApplicants({ features, currentId }) {
  const [items, setItems] = useState(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setItems(null);
    setUnavailable(false);
    postSimilar(features, 6)
      .then((data) => {
        if (cancelled) return;
        setItems((data.items || []).filter((it) => it.id !== currentId));
      })
      .catch(() => {
        if (!cancelled) setUnavailable(true);
      });
    return () => {
      cancelled = true;
    };
  }, [features, currentId]);

  if (unavailable) return null;

  return (
    <div className="card p-5">
      <h3 className="mb-1 text-sm font-semibold text-white">Comparable Past Applicants</h3>
      <p className="mb-4 text-xs text-slate-500">Nearest precedents by model feature similarity (pgvector cosine).</p>

      {items === null && <p className="text-sm text-slate-500">Searching…</p>}

      {items && items.length === 0 && (
        <p className="text-sm text-slate-500">No comparable cases yet — seed precedents or save more assessments.</p>
      )}

      {items && items.length > 0 && (
        <ul className="space-y-3">
          {items.map((it) => {
            const theme = riskTheme(it.risk_category);
            return (
              <li key={it.id} className="rounded-xl border border-ink-600 bg-ink-700/40 p-3">
                {/* Top row: case id + match % */}
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="font-mono text-xs text-slate-400">{it.case_id || `#${it.id.slice(0, 6)}`}</span>
                  <span className="text-sm font-bold text-accent-soft">{(it.similarity * 100).toFixed(0)}% match</span>
                </div>

                {/* Middle row: score + outcome/decision badges */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`text-sm font-semibold ${theme.text}`}>
                    {it.risk_score.toFixed(1)} · {it.risk_category}
                  </span>
                  <OutcomeBadge outcome={it.outcome} />
                  {it.decision && (
                    <span className="rounded-full bg-ink-600 px-2 py-0.5 text-[10px] font-medium text-slate-300">
                      {it.decision}
                    </span>
                  )}
                </div>

                {/* Similarity drivers */}
                {it.similarity_drivers?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-[10px] uppercase tracking-wide text-slate-600">Similarity drivers</p>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {it.similarity_drivers.map((d, i) => (
                        <span key={i} className="rounded-md bg-ink-800 px-2 py-0.5 text-[11px] text-slate-300">
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
