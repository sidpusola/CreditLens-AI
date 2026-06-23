# CreditLens AI — Loan Default Risk & Underwriting Intelligence

End-to-end credit-risk platform that **scores** loan-default risk, **explains** every decision with SHAP, **retrieves comparable precedents** via vector search, and **auto-generates underwriting memos** with an LLM (RAG).

> Tabular ML **+** NLP/LLM **+** full-stack **+** vector database — one cohesive system.

<!-- Add your screenshots here -->
<!-- ![Dashboard](docs/dashboard.png) -->
<!-- ![Risk Report](docs/risk-report.png) -->

**Live demo:** _add your Vercel URL here_ · **API docs:** _add your Render URL_/docs

---

## What it does

| Capability | How |
|---|---|
| **Default-risk score** | XGBoost on the Home Credit dataset — **ROC-AUC 0.7773** |
| **Explainability** | SHAP global + per-applicant risk / protective factors |
| **Officer workflow** | Approve / Manual Review / Reject / Request Docs, with model-override tracking |
| **Comparable cases** | pgvector cosine similarity over the model's feature space, with similarity drivers + real outcomes |
| **AI underwriting memo** | RAG: prediction + SHAP + similar cases → LLM-written credit memo (Qwen local / Groq cloud) |
| **Persistence** | Every assessment + decision stored in Supabase (Postgres) |

## Architecture

```
┌─────────────┐     HTTPS      ┌──────────────────────────┐
│  React UI   │  ───────────▶  │      FastAPI backend     │
│ (Vercel)    │                │                          │
└─────────────┘                │  XGBoost  → risk score   │
                               │  SHAP     → explanation  │
                               │  pgvector → similar cases│
                               │  LLM(RAG) → memo         │
                               └─────────┬────────────────┘
                                         │
                              ┌──────────▼──────────┐   ┌──────────────┐
                              │ Supabase (Postgres  │   │ LLM provider │
                              │  + pgvector)        │   │ Ollama/Groq  │
                              └─────────────────────┘   └──────────────┘
```

## Tech stack

**ML:** Python, pandas, scikit-learn, XGBoost, SHAP
**Backend:** FastAPI, Pydantic, httpx, pytest
**Frontend:** React, Vite, Tailwind CSS
**Data:** Supabase (Postgres + pgvector)
**LLM:** Ollama (Qwen 4B, local) / Groq (Llama, cloud) — RAG

## The model

- **Dataset:** Home Credit Default Risk — 307K applicants across 7 tables (~8% default rate).
- **Feature engineering:** aggregated 5 supplemental sources to applicant level (bureau, previous applications, installments, credit card, POS). A 6th (bureau_balance) was **evaluated and discarded** — it *reduced* ROC-AUC, a deliberate, metrics-driven call.
- **Progression:** baseline `0.7568` → +bureau `0.7621` → +prev_app `0.7676` → +installments `0.7721` → +credit_card `0.7742` → **+POS `0.7773`** (best).
- **Production model:** XGBoost, 454 features, frozen to `backend/models/`.

## Repository layout

```
ml/         training, feature engineering, SHAP, model freezing, precedent seeding
backend/    FastAPI app (routes / services / schemas), SQL migrations, tests
frontend/   React + Vite + Tailwind dashboard
```

## Run locally

**Prerequisites:** Python 3.10, Node 18+, (optional) Ollama for the local LLM.

```bash
# 1. Backend
pip install -r requirements.txt
uvicorn backend.app:app --reload          # http://127.0.0.1:8000/docs

# 2. Frontend
cd frontend
npm install
npm run dev                                # http://localhost:5173
```

The model artifacts are committed, so the API works out of the box. Supabase, pgvector,
and the LLM memo are optional and degrade gracefully (see `backend/.env.example`).
To retrain from scratch: `python ml/preprocess.py` → `ml/train_baseline.py` → `ml/freeze_production.py`.

### Optional integrations
- **Supabase persistence** — create a project, run `backend/db/schema.sql`, set `SUPABASE_URL` / `SUPABASE_KEY`.
- **pgvector similarity** — run `backend/db/pgvector.sql`, set `ENABLE_VECTOR_SEARCH=true`, then `python ml/seed_precedents.py`.
- **LLM memo** — local: install Ollama + `ollama pull qwen3:4b`. Cloud: `LLM_PROVIDER=groq` + `GROQ_API_KEY`.

## Deploy (free tier)

See [DEPLOY.md](DEPLOY.md) for the full step-by-step. In short:
- **Backend → Render** (Docker, `render.yaml` included) with Groq as the cloud LLM.
- **Frontend → Vercel** (root directory `frontend`, env `VITE_API_URL` = your Render URL).
- **Database → Supabase** (already cloud).

## API endpoints

`GET /health` · `GET /model-info` · `POST /predict` · `POST /explain` ·
`POST /assessments` (+ `/similar`, `/{id}/decision`) · `POST /report`

Interactive docs at `/docs`.

---

Built by [@sidpusola](https://github.com/sidpusola).
