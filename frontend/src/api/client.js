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

export async function postAssessment(features) {
  const { data } = await api.post("/assessments", { features });
  return data; // saved DB record (includes id + created_at)
}

export async function getAssessments(limit = 25) {
  const { data } = await api.get("/assessments", { params: { limit } });
  return data; // { count, items: [...] }
}

export async function getAssessment(id) {
  const { data } = await api.get(`/assessments/${id}`);
  return data;
}

export default api;
