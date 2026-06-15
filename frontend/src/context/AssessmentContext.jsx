import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getAssessments } from "../api/client";

// Persists assessments to localStorage (offline fallback) and, when Supabase is
// configured on the backend, syncs history from the server so it is shared
// across sessions and devices. The "current" record is the one being viewed.
const AssessmentContext = createContext(null);
const STORAGE_KEY = "creditlens.assessments.v1";
const MAX_HISTORY = 25;

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

// Map a Supabase row into the internal assessment record shape.
export function serverRecordToEntry(row) {
  return {
    id: row.id,
    submittedAt: row.created_at,
    persisted: true,
    prediction: {
      risk_score: row.risk_score,
      default_probability: row.default_probability,
      risk_category: row.risk_category,
    },
    explanation: {
      risk_score: row.risk_score,
      top_risk_factors: row.top_risk_factors || [],
      top_protective_factors: row.top_protective_factors || [],
    },
    features: row.inputs || {},
  };
}

export function AssessmentProvider({ children }) {
  const [history, setHistory] = useState(loadHistory);
  const [currentId, setCurrentId] = useState(() => loadHistory()[0]?.id ?? null);
  const [persistenceEnabled, setPersistenceEnabled] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch {
      /* ignore quota errors */
    }
  }, [history]);

  // Best-effort sync from Supabase on mount. If persistence is off (503) or the
  // backend is unreachable, we silently keep the localStorage history.
  useEffect(() => {
    let cancelled = false;
    getAssessments(25)
      .then((data) => {
        if (cancelled || !data?.items?.length) return;
        setPersistenceEnabled(true);
        setHistory(data.items.map(serverRecordToEntry));
      })
      .catch(() => {
        /* persistence disabled or offline — keep local history */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Add a new assessment, make it current, and keep history bounded.
  const addAssessment = (record) => {
    const id =
      (typeof crypto !== "undefined" && crypto.randomUUID && crypto.randomUUID()) ||
      String(Date.now());
    const entry = { id, submittedAt: new Date().toISOString(), ...record };
    setHistory((h) => [entry, ...h].slice(0, MAX_HISTORY));
    setCurrentId(id);
    return entry;
  };

  const selectAssessment = (id) => setCurrentId(id);

  const clearHistory = () => {
    setHistory([]);
    setCurrentId(null);
  };

  const assessment = useMemo(
    () => history.find((a) => a.id === currentId) ?? history[0] ?? null,
    [history, currentId]
  );

  return (
    <AssessmentContext.Provider
      value={{ assessment, history, addAssessment, selectAssessment, clearHistory, persistenceEnabled }}
    >
      {children}
    </AssessmentContext.Provider>
  );
}

export function useAssessment() {
  const ctx = useContext(AssessmentContext);
  if (!ctx) throw new Error("useAssessment must be used within AssessmentProvider");
  return ctx;
}
