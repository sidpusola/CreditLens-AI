import { useAssessment } from "../context/AssessmentContext";
import { riskTheme } from "../utils/format";

export default function HistoryPanel() {
  const { history, assessment, selectAssessment, clearHistory } = useAssessment();

  if (history.length === 0) return null;

  return (
    <div className="card p-4 no-print">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">History</h3>
        <button onClick={clearHistory} className="text-xs text-slate-500 hover:text-rose-400">
          Clear
        </button>
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
                <span className={`shrink-0 text-[10px] font-medium ${theme.text}`}>
                  {h.prediction.risk_category.replace(" Risk", "")}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
