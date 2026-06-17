import { useAssessment } from "../context/AssessmentContext";
import { decisionFor } from "../utils/report";

// The four officer actions. `value` is what gets persisted.
const ACTIONS = [
  { value: "Approved", label: "Approve", icon: "M5 13l4 4L19 7", tone: "emerald" },
  { value: "Manual Review", label: "Manual Review", icon: "M12 9v4m0 4h.01M10.3 3.9l-8 14A2 2 0 004 21h16a2 2 0 001.7-3.1l-8-14a2 2 0 00-3.4 0z", tone: "amber" },
  { value: "Rejected", label: "Reject", icon: "M6 18L18 6M6 6l12 12", tone: "rose" },
  { value: "Documents Requested", label: "Request Documents", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h7l5 5v11a2 2 0 01-2 2z", tone: "sky" },
];

const TONES = {
  emerald: { base: "border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/15", active: "bg-emerald-500 text-white border-emerald-500" },
  amber: { base: "border-amber-500/30 text-amber-300 hover:bg-amber-500/15", active: "bg-amber-500 text-white border-amber-500" },
  rose: { base: "border-rose-500/30 text-rose-300 hover:bg-rose-500/15", active: "bg-rose-500 text-white border-rose-500" },
  sky: { base: "border-sky-500/30 text-sky-300 hover:bg-sky-500/15", active: "bg-sky-500 text-white border-sky-500" },
};

export default function DecisionActions({ assessment }) {
  const { recordDecision } = useAssessment();
  const current = assessment.decision;
  const recommended = decisionFor(assessment.prediction.risk_category).verdict;
  // Map the model's recommendation phrasing to an action value for the "matches/override" hint
  const recoValue =
    recommended === "Approve" ? "Approved" : recommended === "Decline / Escalate" ? "Rejected" : "Manual Review";
  const isOverride = current && current !== recoValue;

  return (
    <div className="card p-5">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-white">Officer Decision</h3>
        <span className="text-xs text-slate-500">
          Model recommends:{" "}
          <span className="font-semibold text-slate-300">{recommended}</span>
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {ACTIONS.map((a) => {
          const tone = TONES[a.tone];
          const active = current === a.value;
          return (
            <button
              key={a.value}
              onClick={() => recordDecision(assessment.id, a.value)}
              className={`flex items-center justify-center gap-2 rounded-xl border px-3 py-3 text-sm font-semibold transition ${
                active ? tone.active : `bg-ink-800 ${tone.base}`
              }`}
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d={a.icon} />
              </svg>
              {a.label}
            </button>
          );
        })}
      </div>

      {current ? (
        <div className="mt-4 flex flex-wrap items-center gap-2 rounded-xl border border-ink-600 bg-ink-900/40 p-3 text-sm">
          <span className="text-slate-400">Decision recorded:</span>
          <span className="font-bold text-white">{current}</span>
          {isOverride && (
            <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-xs font-semibold text-amber-400">
              Override (model said {recommended})
            </span>
          )}
          {assessment.decided_at && (
            <span className="ml-auto text-xs text-slate-500">
              {new Date(assessment.decided_at).toLocaleString()}
            </span>
          )}
        </div>
      ) : (
        <p className="mt-3 text-xs text-slate-500">No decision recorded yet — choose an action above.</p>
      )}
    </div>
  );
}
