from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.schemas.explanation import ModelInfoResponse
from backend.services.model_service import get_model_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["model"])


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    """Return production model metadata (name, ROC-AUC, feature count, training date)."""
    try:
        service = get_model_service()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ModelInfoResponse(**service.model_info())
