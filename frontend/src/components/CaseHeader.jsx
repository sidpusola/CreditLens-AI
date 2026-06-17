function fmtMoney(v) {
  if (v == null) return "—";
  return "₹" + Number(v).toLocaleString("en-IN");
}

function Field({ label, value }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-slate-100">{value || "—"}</p>
    </div>
  );
}

// Case-file header: makes the report read like an applicant file, not a model dump.
export default function CaseHeader({ caseMeta = {}, submittedAt }) {
  const name = caseMeta.applicant_name || "Unnamed Applicant";
  const initials = name.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();
  const appDate = caseMeta.application_date || submittedAt;

  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap items-center gap-4 border-b border-ink-700 bg-gradient-to-r from-accent/15 to-transparent p-5">
        <div className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-accent/20 text-lg font-bold text-accent-soft">
          {initials || "?"}
        </div>
        <div className="min-w-0">
          <h2 className="truncate text-xl font-bold text-white">{name}</h2>
          <p className="text-xs text-slate-400">
            Case {caseMeta.applicant_id || "—"}
            {caseMeta.loan_purpose ? ` · ${caseMeta.loan_purpose}` : ""}
          </p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-[11px] uppercase tracking-wide text-slate-500">Loan Amount</p>
          <p className="text-lg font-bold text-white">{fmtMoney(caseMeta.loan_amount)}</p>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 p-5 sm:grid-cols-4">
        <Field label="Applicant ID" value={caseMeta.applicant_id} />
        <Field label="Loan Purpose" value={caseMeta.loan_purpose} />
        <Field label="Application Date" value={appDate ? new Date(appDate).toLocaleDateString() : null} />
        <Field label="Assigned Officer" value={caseMeta.officer_name} />
      </div>
    </div>
  );
}
