from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routes import explain, health, model_info, predict
from backend.utils.logging_config import configure_logging

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Eagerly load the model at startup so the first request isn't slow."""
    try:
        from backend.services.model_service import get_model_service

        get_model_service()
        logger.info("Model warmed up and ready")
    except Exception as exc:
        # Don't crash the app — /health will report degraded until artifacts exist
        logger.warning("Startup warm-up skipped: %s", exc)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered loan underwriting and risk intelligence. "
        "Serves the production XGBoost default-risk model with SHAP explanations."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(predict.router)
app.include_router(explain.router)
app.include_router(model_info.router)


@app.get("/", tags=["root"])
def root() -> dict:
    """Service banner with links to the interactive docs."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "endpoints": ["/health", "/predict", "/explain", "/model-info"],
    }
