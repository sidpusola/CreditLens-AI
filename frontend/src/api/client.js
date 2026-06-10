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

export default api;
