from __future__ import annotations

import logging

from fastapi import APIRouter

from backend.schemas.explanation import HealthResponse
from backend.services.model_service import get_model_service
from backend.services.supabase_service import get_supabase_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness probe. Reports whether the model is loaded and persistence is configured."""
    try:
        get_model_service()
        model_loaded = True
    except Exception as exc:  # artifacts missing or failed to load
        logger.warning("Health check: model not loaded (%s)", exc)
        model_loaded = False

    persistence_enabled = get_supabase_service().enabled
    return HealthResponse(
        status="ok" if model_loaded else "degraded",
        model_loaded=model_loaded,
        persistence_enabled=persistence_enabled,
    )
