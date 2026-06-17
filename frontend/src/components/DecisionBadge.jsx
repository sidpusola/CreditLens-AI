const STYLES = {
  Approved: "bg-emerald-500/15 text-emerald-400",
  "Manual Review": "bg-amber-500/15 text-amber-400",
  Rejected: "bg-rose-500/15 text-rose-400",
  "Documents Requested": "bg-sky-500/15 text-sky-400",
};

const SHORT = {
  Approved: "Approved",
  "Manual Review": "Review",
  Rejected: "Rejected",
  "Documents Requested": "Docs",
};

export default function DecisionBadge({ decision, short = false }) {
  if (!decision) return null;
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${STYLES[decision] || "bg-slate-500/15 text-slate-400"}`}>
      {short ? SHORT[decision] || decision : decision}
    </span>
  );
}
