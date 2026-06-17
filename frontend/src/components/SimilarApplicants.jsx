import { useEffect, useState } from "react";
import { postSimilar } from "../api/client";
import { riskTheme } from "../utils/format";

// Shows pgvector nearest-neighbour historical applicants. Renders nothing when
// vector search is disabled (503) or there are no other comparable records.
export default function SimilarApplicants({ features, currentId }) {
  const [items, setItems] = useState(null); // null = loading, [] = none, [...] = results
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setItems(null);
    setUnavailable(false);
    postSimilar(features, 6)
      .then((data) => {
        if (cancelled) return;
        // Drop the current assessment itself (it matches with similarity ~1.0)
        const filtered = (data.items || []).filter((it) => it.id !== currentId);
        setItems(filtered);
      })
      .catch(() => {
        if (!cancelled) setUnavailable(true);
      });
    return () => {
      cancelled = true;
    };
  }, [features, currentId]);

  // Hidden entirely when the feature is off or errored
  if (unavailable) return null;

  return (
    <div className="card p-5">
      <h3 className="mb-1 text-sm font-semibold text-white">Similar Past Applicants</h3>
      <p className="mb-4 text-xs text-slate-500">
        Nearest historical cases by model feature similarity (pgvector cosine).
      </p>

      {items === null && <p className="text-sm text-slate-500">Searching…</p>}

      {items && items.length === 0 && (
        <p className="text-sm text-slate-500">
          No comparable cases yet — similar applicants will appear as more assessments are saved.
        </p>
      )}

      {items && items.length > 0 && (
        <ul className="space-y-2">
          {items.map((it) => {
            const theme = riskTheme(it.risk_category);
            return (
              <li
                key={it.id}
                className="flex items-center justify-between rounded-xl border border-ink-600 bg-ink-700/50 p-3"
              >
                <div className="min-w-0">
                  <p className={`text-sm font-semibold ${theme.text}`}>
                    {it.risk_score.toFixed(1)} · {it.risk_category}
                  </p>
                  <p className="truncate text-[11px] text-slate-500">
                    {it.created_at ? new Date(it.created_at).toLocaleDateString() : ""}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-accent-soft">
                    {(it.similarity * 100).toFixed(0)}%
                  </p>
                  <p className="text-[10px] text-slate-500">match</p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
