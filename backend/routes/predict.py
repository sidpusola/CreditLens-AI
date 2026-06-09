from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.schemas.prediction import PredictRequest, PredictResponse
from backend.services.model_service import get_model_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    """Score an applicant's default risk."""
    try:
        service = get_model_service()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        result = service.predict(request.features)
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    return PredictResponse(**result)
