// Map a risk category to a consistent color treatment across the UI.
export function riskTheme(category) {
  switch (category) {
    case "High Risk":
      return { text: "text-rose-400", ring: "#fb7185", bg: "bg-rose-500/10", border: "border-rose-500/30" };
    case "Medium Risk":
      return { text: "text-amber-400", ring: "#fbbf24", bg: "bg-amber-500/10", border: "border-amber-500/30" };
    default:
      return { text: "text-emerald-400", ring: "#34d399", bg: "bg-emerald-500/10", border: "border-emerald-500/30" };
  }
}

// ---- Human-friendly feature names ----
// Exact labels for real (numeric / engineered) features, and base columns that
// remain after stripping a one-hot value suffix.
const LABELS = {
  // Application — external scores & amounts
  EXT_SOURCE_1: "External Credit Score 1",
  EXT_SOURCE_2: "External Credit Score 2",
  EXT_SOURCE_3: "External Credit Score 3",
  AMT_CREDIT: "Loan Amount",
  AMT_ANNUITY: "Loan Annuity",
  AMT_GOODS_PRICE: "Goods Price",
  AMT_INCOME_TOTAL: "Total Income",
  // Application — demographics / timing
  DAYS_BIRTH: "Age",
  DAYS_EMPLOYED: "Employment Length",
  DAYS_ID_PUBLISH: "ID Issued (recency)",
  DAYS_REGISTRATION: "Registration (recency)",
  DAYS_LAST_PHONE_CHANGE: "Phone Changed (recency)",
  OWN_CAR_AGE: "Car Age",
  CNT_CHILDREN: "Number of Children",
  CNT_FAM_MEMBERS: "Family Size",
  REGION_POPULATION_RELATIVE: "Region Affluence",
  // Social circle / bureau inquiries
  DEF_60_CNT_SOCIAL_CIRCLE: "Social Circle Delinquency (60d)",
  DEF_30_CNT_SOCIAL_CIRCLE: "Social Circle Delinquency (30d)",
  OBS_60_CNT_SOCIAL_CIRCLE: "Social Circle Observed (60d)",
  OBS_30_CNT_SOCIAL_CIRCLE: "Social Circle Observed (30d)",
  AMT_REQ_CREDIT_BUREAU_QRT: "Bureau Inquiries (Quarter)",
  AMT_REQ_CREDIT_BUREAU_YEAR: "Bureau Inquiries (Year)",
  AMT_REQ_CREDIT_BUREAU_MON: "Bureau Inquiries (Month)",
  REGION_RATING_CLIENT: "Region Rating",
  REGION_RATING_CLIENT_W_CITY: "Region Rating (City)",
  // Bureau aggregates
  bureau_debt_to_credit: "Bureau Debt-to-Credit Ratio",
  bureau_total_loans: "Total Bureau Loans",
  bureau_active_count: "Active Bureau Loans",
  bureau_closed_count: "Closed Bureau Loans",
  bureau_total_debt: "Total Bureau Debt",
  bureau_total_credit: "Total Bureau Credit",
  bureau_max_overdue: "Max Bureau Overdue",
  bureau_avg_overdue: "Avg Bureau Overdue",
  bureau_avg_credit_age: "Avg Bureau Credit Age",
  // Previous applications
  prev_refusal_ratio: "Past Refusal Rate",
  prev_approval_ratio: "Past Approval Rate",
  prev_canceled_ratio: "Past Cancellation Rate",
  prev_app_count: "Prior Applications",
  prev_amt_down_payment_mean: "Avg Down Payment (prior)",
  prev_amt_credit_mean: "Avg Prior Credit",
  prev_consumer_loans_count: "Prior Consumer Loans",
  prev_revolving_loans_count: "Prior Revolving Loans",
  prev_cash_loans_count: "Prior Cash Loans",
  // Installment behaviour
  late_payment_ratio: "Late Payment Rate",
  max_days_late: "Worst Days Late",
  avg_days_late: "Avg Days Late",
  total_installment_amount: "Total Installments Paid",
  max_installment_amount: "Largest Installment",
  avg_payment_ratio: "Avg Payment Coverage",
  avg_payment_recency: "Payment Recency",
  underpayment_count: "Underpayments",
  // Credit card behaviour
  cc_high_utilization_ratio: "High Card-Utilization Rate",
  cc_max_utilization_ratio: "Peak Card Utilization",
  cc_avg_utilization_ratio: "Avg Card Utilization",
  cc_avg_drawings: "Avg Card Drawings",
  cc_active_months: "Active Card Months",
  cc_avg_balance: "Avg Card Balance",
  // POS / cash loans
  pos_remaining_installments_mean: "Avg Remaining Installments",
  pos_remaining_installments_max: "Max Remaining Installments",
  pos_completed_installments_mean: "Avg Completed POS Installments",
  pos_active_loans: "Active POS Loans",
  pos_completed_loans: "Completed POS Loans",
  pos_late_payment_ratio: "POS Late Payment Rate",
};

// Known categorical columns -> rendered as "Label: Value".
const CATEGORICAL = {
  CODE_GENDER: { label: "Gender", values: { M: "Male", F: "Female", XNA: "Unknown" } },
  FLAG_OWN_CAR: { label: "Owns Car", values: { Y: "Yes", N: "No" } },
  FLAG_OWN_REALTY: { label: "Owns Property", values: { Y: "Yes", N: "No" } },
  NAME_EDUCATION_TYPE: { label: "Education" },
  NAME_FAMILY_STATUS: { label: "Family Status" },
  NAME_CONTRACT_TYPE: { label: "Contract Type" },
  NAME_INCOME_TYPE: { label: "Income Type" },
  NAME_HOUSING_TYPE: { label: "Housing Type" },
  OCCUPATION_TYPE: { label: "Occupation" },
  ORGANIZATION_TYPE: { label: "Organization" },
  WALLSMATERIAL_MODE: { label: "Walls Material" },
};

const CAT_KEYS = Object.keys(CATEGORICAL).sort((a, b) => b.length - a.length);

function titleCase(s) {
  return s
    .split("_")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

// True for "absence of a problem" factors (zero-count one-hots) — they read oddly
// as risk drivers, so the decision-framing UI skips them. SHAP charts keep them.
export function isSoftFactor(feature) {
  const h = prettyFeature(feature).toLowerCase();
  return h.startsWith("no ") || h.endsWith("= 0") || h.endsWith(": 0") || h.includes("not on file");
}

export function prettyFeature(name) {
  if (!name) return "";

  // 1. Exact match for real features (protects EXT_SOURCE_1, AMT_*, engineered names)
  if (LABELS[name]) return LABELS[name];

  // 2. Known categorical one-hot -> "Label: Value"
  for (const base of CAT_KEYS) {
    if (name === base) return CATEGORICAL[base].label;
    if (name.startsWith(base + "_")) {
      const raw = name.slice(base.length + 1);
      const cfg = CATEGORICAL[base];
      const val = cfg.values?.[raw] ?? raw;
      return `${cfg.label}: ${val}`;
    }
  }

  // 3. Trailing one-hot value suffix (e.g. _0.0, _3) — keep the value's meaning
  const m = name.match(/^(.*)_(\d+(?:\.\d+)?)$/);
  if (m) {
    const base = m[1];
    const val = parseFloat(m[2]);
    const doc = base.match(/^FLAG_DOCUMENT_(\d+)$/);
    if (doc) return `Document ${doc[1]}: ${val ? "On File" : "Not on File"}`;
    const label = LABELS[base] || titleCase(base);
    const isCount =
      /^(DEF|OBS)_/.test(base) ||
      base.includes("SOCIAL_CIRCLE") ||
      base.startsWith("AMT_REQ_CREDIT_BUREAU") ||
      /delinquency|observation|inquiries/i.test(label);
    if (isCount) return val === 0 ? `No ${label}` : `${label}: ${val}`;
    return `${label}: ${val}`;
  }

  // 4. Fallback: title-case
  return titleCase(name);
}
