import { createContext, useContext, useEffect, useMemo, useState } from "react";

// Persists assessments to localStorage so the Risk Report page can show history
// and survive page reloads. The "current" record is the one being viewed.
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

export function AssessmentProvider({ children }) {
  const [history, setHistory] = useState(loadHistory);
  const [currentId, setCurrentId] = useState(() => loadHistory()[0]?.id ?? null);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch {
      /* ignore quota errors */
    }
  }, [history]);

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
      value={{ assessment, history, addAssessment, selectAssessment, clearHistory }}
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
