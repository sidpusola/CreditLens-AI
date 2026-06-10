export default function StatusPill({ ok, labelOk = "Online", labelBad = "Offline", loading }) {
  if (loading) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full border border-ink-600 bg-ink-700 px-3 py-1 text-xs font-medium text-slate-400">
        <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" /> Checking…
      </span>
    );
  }
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${
        ok
          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
          : "border-rose-500/30 bg-rose-500/10 text-rose-400"
      }`}
    >
      <span className={`h-2 w-2 rounded-full ${ok ? "bg-emerald-400" : "bg-rose-400"}`} />
      {ok ? labelOk : labelBad}
    </span>
  );
}
