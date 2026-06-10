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

// Turn raw model feature names into something human-readable.
const NICE = {
  EXT_SOURCE_1: "External Score 1",
  EXT_SOURCE_2: "External Score 2",
  EXT_SOURCE_3: "External Score 3",
  AMT_CREDIT: "Credit Amount",
  AMT_ANNUITY: "Loan Annuity",
  AMT_GOODS_PRICE: "Goods Price",
  DAYS_BIRTH: "Age",
  DAYS_EMPLOYED: "Employment Length",
  late_payment_ratio: "Late Payment Ratio",
  bureau_debt_to_credit: "Bureau Debt/Credit",
  prev_refusal_ratio: "Past Refusal Ratio",
  pos_remaining_installments_mean: "Avg Remaining Installments",
  cc_high_utilization_ratio: "High Card Utilization Ratio",
  NAME_EDUCATION_TYPE: "Education",
  NAME_CONTRACT_TYPE: "Contract Type",
  CODE_GENDER: "Gender",
};

export function prettyFeature(name) {
  if (NICE[name]) return NICE[name];
  // Strip one-hot suffix like "NAME_CONTRACT_TYPE_Cash loans"
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
