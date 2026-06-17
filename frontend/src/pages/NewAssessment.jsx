import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { postPredict, postExplain, postAssessment } from "../api/client";
import { useAssessment, serverRecordToEntry } from "../context/AssessmentContext";

// Curated, human-friendly inputs. Anything not provided is imputed by the backend.
const NUMERIC_FIELDS = [
  { key: "EXT_SOURCE_1", label: "External Score 1", min: 0, max: 1, step: 0.01, hint: "0–1" },
  { key: "EXT_SOURCE_2", label: "External Score 2", min: 0, max: 1, step: 0.01, hint: "0–1" },
  { key: "EXT_SOURCE_3", label: "External Score 3", min: 0, max: 1, step: 0.01, hint: "0–1" },
  { key: "AMT_CREDIT", label: "Credit Amount", step: 1000, hint: "loan size" },
  { key: "AMT_ANNUITY", label: "Loan Annuity", step: 1000, hint: "yearly payment" },
  { key: "AMT_GOODS_PRICE", label: "Goods Price", step: 1000, hint: "" },
  { key: "late_payment_ratio", label: "Late Payment Ratio", min: 0, max: 1, step: 0.01, hint: "0–1" },
  { key: "bureau_debt_to_credit", label: "Bureau Debt / Credit", min: 0, step: 0.01, hint: "" },
  { key: "prev_refusal_ratio", label: "Past Refusal Ratio", min: 0, max: 1, step: 0.01, hint: "0–1" },
  { key: "cc_high_utilization_ratio", label: "High Card Utilization", min: 0, max: 1, step: 0.01, hint: "0–1" },
];

const EDUCATION_OPTIONS = [
  "Higher education",
  "Secondary / secondary special",
  "Incomplete higher",
  "Lower secondary",
  "Academic degree",
];

const rand = (min, max, decimals = 2) => {
  const v = min + Math.random() * (max - min);
  const f = 10 ** decimals;
  return Math.round(v * f) / f;
};
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
const round1000 = (v) => Math.round(v / 1000) * 1000;

// Generate a fresh, realistic applicant. Profiles are randomly skewed toward
// "strong" or "weak" so each click can yield a different risk outcome.
function generateSample() {
  const strong = Math.random() > 0.5;
  const ext = () => (strong ? rand(0.45, 0.85) : rand(0.02, 0.35));
  const credit = round1000(rand(100000, 1800000));
  return {
    age: Math.round(rand(21, 65, 0)),
    employmentYears: Math.round(rand(0, 25, 0)),
    CODE_GENDER: pick(["M", "F"]),
    NAME_EDUCATION_TYPE: pick(EDUCATION_OPTIONS),
    NAME_CONTRACT_TYPE: pick(["Cash loans", "Revolving loans"]),
    EXT_SOURCE_1: ext(),
    EXT_SOURCE_2: ext(),
    EXT_SOURCE_3: ext(),
    AMT_CREDIT: credit,
    AMT_ANNUITY: round1000(credit / rand(15, 30)),
    AMT_GOODS_PRICE: round1000(credit * rand(0.85, 1.0)),
    late_payment_ratio: strong ? rand(0, 0.15) : rand(0.3, 0.9),
    bureau_debt_to_credit: strong ? rand(0, 0.4) : rand(0.5, 1.4),
    prev_refusal_ratio: strong ? rand(0, 0.2) : rand(0.3, 0.8),
    cc_high_utilization_ratio: strong ? rand(0, 0.3) : rand(0.5, 1.0),
  };
}

const EMPTY = {
  age: "",
  employmentYears: "",
  CODE_GENDER: "M",
  NAME_EDUCATION_TYPE: "Higher education",
  NAME_CONTRACT_TYPE: "Cash loans",
};

export default function NewAssessment() {
  const [form, setForm] = useState(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const { addAssessment } = useAssessment();
  const navigate = useNavigate();

  const update = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const buildFeatures = () => {
    const features = {};
    // Numeric model features
    NUMERIC_FIELDS.forEach(({ key }) => {
      if (form[key] !== "" && form[key] !== undefined) features[key] = parseFloat(form[key]);
    });
    // Categorical
    if (form.CODE_GENDER) features.CODE_GENDER = form.CODE_GENDER;
    if (form.NAME_EDUCATION_TYPE) features.NAME_EDUCATION_TYPE = form.NAME_EDUCATION_TYPE;
    if (form.NAME_CONTRACT_TYPE) features.NAME_CONTRACT_TYPE = form.NAME_CONTRACT_TYPE;
    // Derived: convert human units to the model's day-based columns (negative = in the past)
    if (form.age !== "" && form.age !== undefined) features.DAYS_BIRTH = -Math.round(parseFloat(form.age) * 365);
    if (form.employmentYears !== "" && form.employmentYears !== undefined)
      features.DAYS_EMPLOYED = -Math.round(parseFloat(form.employmentYears) * 365);
    return features;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const features = buildFeatures();
      // Prefer the persisted path (scores + saves to Supabase). If persistence is
      // unavailable for any reason (503 not configured, older backend, offline),
      // fall back to stateless predict + explain so the app still works.
      try {
        const saved = await postAssessment(features);
        addAssessment({ ...serverRecordToEntry(saved), features });
      } catch {
        const [prediction, explanation] = await Promise.all([
          postPredict(features),
          postExplain(features),
        ]);
        addAssessment({ prediction, explanation, features, persisted: false });
      }
      navigate("/report");
    } catch (err) {
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">New Assessment</h1>
          <p className="text-sm text-slate-400">Score an applicant's probability of default</p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => setForm(generateSample())} className="rounded-xl border border-ink-600 bg-ink-700 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-ink-600">
            Load sample
          </button>
          <button type="button" onClick={() => setForm(EMPTY)} className="rounded-xl border border-ink-600 bg-ink-700 px-3 py-2 text-sm font-medium text-slate-300 hover:bg-ink-600">
            Clear
          </button>
        </div>
      </div>

      {error && (
        <div className="card mb-6 border-rose-500/30 bg-rose-500/5 p-4 text-sm text-rose-300">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="card p-6">
        <p className="mb-4 text-xs text-slate-500">
          Fill any subset — blank fields are imputed by the model pipeline. Strong predictors are the External Scores
          and Late Payment Ratio.
        </p>

        {/* Applicant profile */}
        <h3 className="mb-3 text-sm font-semibold text-accent-soft">Applicant Profile</h3>
        <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-3">
          <div>
            <label className="label">Age (years)</label>
            <input className="input" type="number" value={form.age} onChange={(e) => update("age", e.target.value)} placeholder="34" />
          </div>
          <div>
            <label className="label">Employment (years)</label>
            <input className="input" type="number" value={form.employmentYears} onChange={(e) => update("employmentYears", e.target.value)} placeholder="3" />
          </div>
          <div>
            <label className="label">Gender</label>
            <select className="input" value={form.CODE_GENDER} onChange={(e) => update("CODE_GENDER", e.target.value)}>
              <option value="M">Male</option>
              <option value="F">Female</option>
            </select>
          </div>
          <div className="col-span-2">
            <label className="label">Education</label>
            <select className="input" value={form.NAME_EDUCATION_TYPE} onChange={(e) => update("NAME_EDUCATION_TYPE", e.target.value)}>
              <option>Higher education</option>
              <option>Secondary / secondary special</option>
              <option>Incomplete higher</option>
              <option>Lower secondary</option>
              <option>Academic degree</option>
            </select>
          </div>
          <div>
            <label className="label">Contract Type</label>
            <select className="input" value={form.NAME_CONTRACT_TYPE} onChange={(e) => update("NAME_CONTRACT_TYPE", e.target.value)}>
              <option>Cash loans</option>
              <option>Revolving loans</option>
            </select>
          </div>
        </div>

        {/* Financial & behavioral signals */}
        <h3 className="mb-3 text-sm font-semibold text-accent-soft">Financial & Behavioral Signals</h3>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          {NUMERIC_FIELDS.map((f) => (
            <div key={f.key}>
              <label className="label">{f.label}{f.hint && <span className="ml-1 normal-case text-slate-600">({f.hint})</span>}</label>
              <input
                className="input"
                type="number"
                step={f.step}
                min={f.min}
                max={f.max}
                value={form[f.key] ?? ""}
                onChange={(e) => update(f.key, e.target.value)}
              />
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end">
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting ? "Scoring…" : "Run Assessment"}
            {!submitting && (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14m-6-6l6 6-6 6" />
              </svg>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
