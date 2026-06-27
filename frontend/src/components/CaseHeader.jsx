function fmtMoney(v) {
  if (v == null) return "—";
  return "₹" + Number(v).toLocaleString("en-IN");
}

// Indian-style short money: ₹9.2L, ₹1.4Cr
function fmtShortINR(v) {
  if (v == null || v === "") return null;
  const n = Number(v);
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(1)}Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(1)}L`;
  return `₹${n.toLocaleString("en-IN")}`;
}

function Field({ label, value }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-slate-100">{value || "—"}</p>
    </div>
  );
}

function StatTile({ label, value }) {
  return (
    <div className="rounded-xl border border-ink-600 bg-ink-700/40 p-3">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-base font-bold text-white">{value ?? "—"}</p>
    </div>
  );
}

// Case-file header: applicant identity + the underwriting facts officers actually care about.
export default function CaseHeader({ caseMeta = {}, features = {}, submittedAt }) {
  const name = caseMeta.applicant_name || "Unnamed Applicant";
  const initials = name.split(" ").map((w) => w[0]).slice(0, 2).join("").toUpperCase();
  const appDate = caseMeta.application_date || submittedAt;

  // Derive the underwriting summary from the model inputs
  const age = features.DAYS_BIRTH != null ? Math.round(-features.DAYS_BIRTH / 365) : null;
  const employment = features.DAYS_EMPLOYED != null ? Math.round(-features.DAYS_EMPLOYED / 365) : null;
  const debtRatio = features.bureau_debt_to_credit != null ? Math.round(features.bureau_debt_to_credit * 100) : null;
  const prevLoans = features.prev_app_count != null ? Math.round(features.prev_app_count) : null;
  const income = fmtShortINR(features.AMT_INCOME_TOTAL);

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

      {/* Underwriting summary — the financial profile */}
      <div className="grid grid-cols-2 gap-3 p-5 sm:grid-cols-3 lg:grid-cols-5">
        <StatTile label="Income" value={income} />
        <StatTile label="Employment" value={employment != null ? `${employment} yr${employment === 1 ? "" : "s"}` : null} />
        <StatTile label="Debt Ratio" value={debtRatio != null ? `${debtRatio}%` : null} />
        <StatTile label="Previous Loans" value={prevLoans != null ? String(prevLoans) : null} />
        <StatTile label="Age" value={age != null ? String(age) : null} />
      </div>

      {/* Case administration */}
      <div className="grid grid-cols-2 gap-4 border-t border-ink-700 p-5 sm:grid-cols-4">
        <Field label="Applicant ID" value={caseMeta.applicant_id} />
        <Field label="Loan Purpose" value={caseMeta.loan_purpose} />
        <Field label="Application Date" value={appDate ? new Date(appDate).toLocaleDateString() : null} />
        <Field label="Assigned Officer" value={caseMeta.officer_name} />
      </div>
    </div>
  );
}
