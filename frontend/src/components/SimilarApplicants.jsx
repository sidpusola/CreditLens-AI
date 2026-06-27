import { useEffect, useState } from "react";
import { postSimilar } from "../api/client";
import { riskTheme } from "../utils/format";

function OutcomeBadge({ outcome }) {
  if (!outcome) return <span className="text-xs text-slate-500">Pending</span>;
  const defaulted = /default/i.test(outcome);
  return (
    <span className={`text-xs font-bold ${defaulted ? "text-rose-400" : "text-emerald-400"}`}>
      {defaulted ? "Defaulted" : "Repaid"}
    </span>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <div className="mt-0.5 text-sm font-semibold">{children}</div>
    </div>
  );
}

// pgvector nearest-neighbour precedents shown as a case file: decision + outcome + drivers.
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

  // How many of the resolved neighbours defaulted — the headline signal.
  const resolved = (items || []).filter((it) => it.outcome);
  const defaults = resolved.filter((it) => /default/i.test(it.outcome)).length;

  return (
    <div className="card p-5">
      <h3 className="mb-1 text-sm font-semibold text-white">Comparable Past Applicants</h3>
      <p className="mb-3 text-xs text-slate-500">Nearest precedents by model feature similarity (pgvector cosine).</p>

      {resolved.length > 0 && (
        <div className={`mb-4 rounded-xl border p-3 text-sm ${defaults / resolved.length >= 0.5 ? "border-rose-500/30 bg-rose-500/10 text-rose-300" : "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"}`}>
          <span className="font-bold">{defaults} of {resolved.length}</span> similar resolved cases{" "}
          {defaults / resolved.length >= 0.5 ? "defaulted" : "were repaid"}.
        </div>
      )}

      {items === null && <p className="text-sm text-slate-500">Searching…</p>}
      {items && items.length === 0 && (
        <p className="text-sm text-slate-500">No comparable cases yet.</p>
      )}

      {items && items.length > 0 && (
        <ul className="space-y-3">
          {items.map((it) => {
            const theme = riskTheme(it.risk_category);
            return (
              <li key={it.id} className="rounded-xl border border-ink-600 bg-ink-700/40 p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-mono text-xs text-slate-400">
                    Applicant {it.case_id || `#${it.id.slice(0, 6).toUpperCase()}`}
                  </span>
                  <span className="text-sm font-bold text-accent-soft">{(it.similarity * 100).toFixed(0)}%</span>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <Field label="Decision">
                    {it.decision ? <span className="text-slate-200">{it.decision}</span> : <span className="text-slate-500">—</span>}
                  </Field>
                  <Field label="Outcome"><OutcomeBadge outcome={it.outcome} /></Field>
                  <Field label="Risk"><span className={theme.text}>{it.risk_score.toFixed(1)}</span></Field>
                </div>

                {it.similarity_drivers?.length > 0 && (
                  <div className="mt-2.5">
                    <p className="text-[10px] uppercase tracking-wide text-slate-600">Top Similarities</p>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {it.similarity_drivers.map((d, i) => (
                        <span key={i} className="rounded-md bg-ink-800 px-2 py-0.5 text-[11px] text-slate-300">{d}</span>
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
