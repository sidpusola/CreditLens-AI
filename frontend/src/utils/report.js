// Confidence = how far the model is from the 0.5 decision boundary (0-100%).
export function confidenceScore(probability) {
  return Math.round(Math.abs(probability - 0.5) * 2 * 1000) / 10;
}

// Map risk category to an underwriting decision + rationale.
export function decisionFor(category) {
  switch (category) {
    case "High Risk":
      return {
        verdict: "Decline / Escalate",
        tone: "rose",
        blurb:
          "Default probability exceeds the high-risk threshold. Recommend declining or escalating to senior underwriting with additional collateral or guarantor requirements.",
      };
    case "Medium Risk":
      return {
        verdict: "Manual Review",
        tone: "amber",
        blurb:
          "Moderate default probability. Recommend manual review of income documentation and existing obligations before a decision.",
      };
    default:
      return {
        verdict: "Approve",
        tone: "emerald",
        blurb:
          "Default probability is within acceptable limits. Eligible for standard approval, subject to routine verification.",
      };
  }
}

// Trigger a client-side JSON file download for an assessment record.
export function downloadJSON(record) {
  const payload = {
    id: record.id,
    submittedAt: record.submittedAt,
    prediction: record.prediction,
    explanation: record.explanation,
    inputs: record.features ?? {},
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `creditlens-report-${record.id?.slice(0, 8) || "report"}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
