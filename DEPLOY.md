# Deploying CreditLens AI (free tier)

Three pieces: **backend → Render**, **frontend → Vercel**, **database → Supabase** (already cloud).
Total time ~20 minutes. Everything below is free.

## 0. Prerequisites
- Code pushed to GitHub (you have this).
- A **Supabase** project with the migrations run (`schema.sql`, `pgvector.sql`, `case.sql`, `decisions.sql`, `outcome.sql`) and precedents seeded.
- A free **Groq API key** → https://console.groq.com → API Keys → Create.

---

## 1. Backend → Render

1. Go to https://render.com → **New → Web Service** → connect your GitHub repo.
2. Render detects `render.yaml` (Docker). Accept it. Region: any.
3. Under **Environment**, set these (the `sync:false` ones from `render.yaml`):

   | Key | Value |
   |---|---|
   | `SUPABASE_URL` | your Supabase project URL |
   | `SUPABASE_KEY` | your Supabase anon key |
   | `GROQ_API_KEY` | your Groq key |
   | `CREDITLENS_CORS_ORIGINS` | *(leave blank for now — set after step 2)* |

   (`ENABLE_VECTOR_SEARCH`, `LLM_PROVIDER=groq`, `LLM_MODEL` are already in `render.yaml`.)
4. **Create Web Service.** First build takes a few minutes.
5. When live, note the URL, e.g. `https://creditlens-api.onrender.com`.
   Test it: open `https://creditlens-api.onrender.com/health` → should return `model_loaded: true`.

> **Note:** Render's free tier sleeps after ~15 min idle (first request then takes ~30–60s to wake) and has 512 MB RAM. If the service runs out of memory, switch to **Hugging Face Spaces** (Docker, 16 GB free) or Render's $7 Starter plan — the same Dockerfile works on both.

---

## 2. Frontend → Vercel

1. Go to https://vercel.com → **Add New → Project** → import your GitHub repo.
2. **Root Directory:** set to `frontend`.
3. Framework preset: **Vite** (auto-detected). Build command `npm run build`, output `dist` (defaults).
4. **Environment Variables:** add
   | Key | Value |
   |---|---|
   | `VITE_API_URL` | your Render backend URL (e.g. `https://creditlens-api.onrender.com`) |
5. **Deploy.** When live, note the URL, e.g. `https://creditlens-ai.vercel.app`.

---

## 3. Wire CORS (connect the two)

1. Back in **Render → Environment**, set:
   | Key | Value |
   |---|---|
   | `CREDITLENS_CORS_ORIGINS` | your Vercel URL, e.g. `https://creditlens-ai.vercel.app` |
2. Save → Render redeploys automatically.

---

## 4. Verify

Open your Vercel URL and:
- **Dashboard** loads with live model metrics (proves frontend → backend → model).
- **New Assessment → Run** → saves to Supabase (proves DB).
- **Risk Report → Generate Memo** → Groq writes the memo (proves cloud LLM).
- **Comparable Applicants** shows precedents (proves pgvector).

Then update the **Live demo** links at the top of `README.md`.

---

## Troubleshooting
- **CORS error in browser console** → `CREDITLENS_CORS_ORIGINS` doesn't exactly match the Vercel origin (no trailing slash).
- **Memo 503** → `GROQ_API_KEY` missing/invalid, or `LLM_PROVIDER` not `groq`.
- **Backend OOM / crash on Render free** → use Hugging Face Spaces (Docker) or a paid plan.
- **Refresh on `/report` 404s** → ensure `frontend/vercel.json` (SPA rewrite) is committed.
