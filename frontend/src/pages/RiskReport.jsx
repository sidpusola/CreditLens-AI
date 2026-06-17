import { Link } from "react-router-dom";
import { useAssessment } from "../context/AssessmentContext";
import RiskGauge from "../components/RiskGauge";
import RiskFactorCard from "../components/RiskFactorCard";
import ShapWaterfall from "../components/ShapWaterfall";
import FeatureImportanceChart from "../components/FeatureImportanceChart";
import DecisionSummary from "../components/DecisionSummary";
import DecisionActions from "../components/DecisionActions";
import CaseHeader from "../components/CaseHeader";
import HistoryPanel from "../components/HistoryPanel";
import SimilarApplicants from "../components/SimilarApplicants";
import UnderwritingReport from "../components/UnderwritingReport";
import { riskTheme } from "../utils/format";
import { confidenceScore, downloadJSON } from "../utils/report";

function StatTile({ label, value, accent = "text-white" }) {
  return (
    <div className="rounded-xl border border-ink-600 bg-ink-700/50 p-3 text-center">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-lg font-bold ${accent}`}>{value}</p>
    </div>
  );
}

export default function RiskReport() {
  const { assessment } = useAssessment();

  if (!assessment) {
    return (
      <div className="card p-10 text-center">
        <h1 className="text-xl font-bold text-white">No assessment yet</h1>
        <p className="mt-2 text-sm text-slate-400">Run an assessment to generate an underwriting report.</p>
        <Link to="/assess" className="btn-primary mt-5">Go to New Assessment</Link>
      </div>
    );
  }

  const { prediction, explanation } = assessment;
  const theme = riskTheme(prediction.risk_category);
  const confidence = confidenceScore(prediction.default_probability);

  return (
    <div>
      {/* Header + actions */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">Risk Report</h1>
          <p className="text-sm text-slate-400">
            Underwriting decision · {new Date(assessment.submittedAt).toLocaleString()}
          </p>
        </div>
        <div className="flex gap-2 no-print">
          <button onClick={() => window.print()} className="rounded-xl border border-ink-600 bg-ink-700 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-ink-600">
            Export PDF
          </button>
          <button onClick={() => downloadJSON(assessment)} className="rounded-xl border border-ink-600 bg-ink-700 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-ink-600">
            Download JSON
          </button>
          <Link to="/assess" className="btn-primary">New Assessment</Link>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Main report column */}
        <div className="space-y-6 lg:col-span-3">
          {/* Case file header — who & what, first */}
          <CaseHeader caseMeta={assessment.case || {}} submittedAt={assessment.submittedAt} />

          {/* Officer action workflow — the primary call to action */}
          <DecisionActions assessment={assessment} />

          {/* Score + decision */}
          <div className="grid gap-6 md:grid-cols-3">
            <div className="card flex flex-col items-center justify-center p-6">
              <RiskGauge score={prediction.risk_score} category={prediction.risk_category} />
              <div className="mt-5 grid w-full grid-cols-2 gap-2">
                <StatTile label="Risk Score" value={prediction.risk_score.toFixed(1)} accent={theme.text} />
                <StatTile label="Probability" value={`${(prediction.default_probability * 100).toFixed(1)}%`} />
                <StatTile label="Category" value={prediction.risk_category.replace(" Risk", "")} accent={theme.text} />
                <StatTile label="Confidence" value={`${confidence}%`} accent="text-accent-soft" />
              </div>
            </div>
            <div className="md:col-span-2">
              <DecisionSummary prediction={prediction} explanation={explanation} />
            </div>
          </div>

          {/* SHAP charts */}
          <div className="grid gap-6 lg:grid-cols-2">
            <ShapWaterfall
              riskFactors={explanation.top_risk_factors}
              protectiveFactors={explanation.top_protective_factors}
            />
            <FeatureImportanceChart
              riskFactors={explanation.top_risk_factors}
              protectiveFactors={explanation.top_protective_factors}
            />
          </div>

          {/* AI underwriting report (RAG + local LLM) */}
          <UnderwritingReport features={assessment.features || {}} caseMeta={assessment.case || {}} />

          {/* Factor lists */}
          <div className="grid gap-6 md:grid-cols-2">
            <section>
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-rose-400">
                <span className="h-2 w-2 rounded-full bg-rose-400" /> Top 5 Risk Factors
              </h3>
              <div className="space-y-3">
                {explanation.top_risk_factors.map((f, i) => (
                  <RiskFactorCard key={`r-${i}`} factor={f} kind="risk" />
                ))}
              </div>
            </section>
            <section>
              <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-emerald-400">
                <span className="h-2 w-2 rounded-full bg-emerald-400" /> Top 5 Protective Factors
              </h3>
              <div className="space-y-3">
                {explanation.top_protective_factors.map((f, i) => (
                  <RiskFactorCard key={`p-${i}`} factor={f} kind="protective" />
                ))}
              </div>
            </section>
          </div>
        </div>

        {/* Right rail: similar applicants + history */}
        <div className="space-y-6 lg:col-span-1">
          <SimilarApplicants features={assessment.features || {}} currentId={assessment.id} />
          <HistoryPanel />
        </div>
      </div>

      <p className="mt-6 text-center text-xs text-slate-600">
        Impacts are SHAP values (log-odds contribution) · CreditLens AI · XGBoost production model
      </p>
    </div>
  );
}
