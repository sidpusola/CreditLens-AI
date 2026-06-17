import axios from "axios";

// In dev, calls go through the Vite proxy (/api -> FastAPI). Override with VITE_API_URL if needed.
const baseURL = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({ baseURL, timeout: 30000 });

export async function getHealth() {
  const { data } = await api.get("/health");
  return data;
}

export async function getModelInfo() {
  const { data } = await api.get("/model-info");
  return data;
}

export async function postPredict(features) {
  const { data } = await api.post("/predict", { features });
  return data;
}

export async function postExplain(features) {
  const { data } = await api.post("/explain", { features });
  return data;
}

// ---- Supabase-backed persistence (gracefully returns 503 if not configured) ----

export async function postAssessment(features, caseMeta = null) {
  const { data } = await api.post("/assessments", { features, case: caseMeta });
  return data; // saved DB record (includes id + created_at + case_meta)
}

export async function getAssessments(limit = 25) {
  const { data } = await api.get("/assessments", { params: { limit } });
  return data; // { count, items: [...] }
}

export async function getAssessment(id) {
  const { data } = await api.get(`/assessments/${id}`);
  return data;
}

export async function postSimilar(features, limit = 5) {
  const { data } = await api.post("/assessments/similar", { features }, { params: { limit } });
  return data; // { count, items: [{ id, risk_score, risk_category, similarity, created_at }] }
}

export async function patchDecision(id, decision, note = null) {
  const { data } = await api.patch(`/assessments/${id}/decision`, { decision, note });
  return data;
}

export async function postReport(features, caseMeta = null, similarCount = 5) {
  // LLM report generation can take a while on local hardware — allow more time.
  const { data } = await api.post(
    "/report",
    { features, case: caseMeta },
    { params: { similar_count: similarCount }, timeout: 180000 }
  );
  return data; // { report, model, risk_score, risk_category, similar_used }
}

export default api;
