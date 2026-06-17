import { useAssessment } from "../context/AssessmentContext";
import { riskTheme } from "../utils/format";
import DecisionBadge from "./DecisionBadge";

export default function HistoryPanel() {
  const { history, assessment, selectAssessment, clearHistory, persistenceEnabled } = useAssessment();

  if (history.length === 0) return null;

  return (
    <div className="card p-4 no-print">
      <div className="mb-1 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">History</h3>
        <button onClick={clearHistory} className="text-xs text-slate-500 hover:text-rose-400">
          Clear
        </button>
      </div>
      <div className="mb-3">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium ${
            persistenceEnabled
              ? "bg-emerald-500/10 text-emerald-400"
              : "bg-slate-500/10 text-slate-400"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${persistenceEnabled ? "bg-emerald-400" : "bg-slate-400"}`} />
          {persistenceEnabled ? "Cloud synced" : "Local only"}
        </span>
      </div>
      <ul className="space-y-1.5">
        {history.map((h) => {
          const active = h.id === assessment?.id;
          const theme = riskTheme(h.prediction.risk_category);
          return (
            <li key={h.id}>
              <button
                onClick={() => selectAssessment(h.id)}
                className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left transition ${
                  active ? "bg-accent/15" : "hover:bg-ink-700"
                }`}
              >
                <div className="min-w-0">
                  <p className={`text-sm font-semibold ${theme.text}`}>
                    {h.prediction.risk_score.toFixed(1)}
                  </p>
                  <p className="truncate text-[11px] text-slate-500">
                    {new Date(h.submittedAt).toLocaleString()}
                  </p>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1">
                  <span className={`text-[10px] font-medium ${theme.text}`}>
                    {h.prediction.risk_category.replace(" Risk", "")}
                  </span>
                  <DecisionBadge decision={h.decision} short />
                </div>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
