# CreditLens AI — backend (FastAPI) container
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# System libs some ML wheels need at runtime (libgomp for xgboost)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# App code + the ml package (backend imports ml.explain) + frozen model artifacts
COPY backend/ ./backend/
COPY ml/ ./ml/

EXPOSE 8000

# Honour the platform's $PORT (Render/Railway set it); default 8000 locally.
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
