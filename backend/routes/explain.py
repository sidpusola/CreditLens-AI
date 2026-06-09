from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.schemas.explanation import ExplainResponse
from backend.schemas.prediction import PredictRequest
from backend.services.model_service import get_model_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["explanation"])


@router.post("/explain", response_model=ExplainResponse)
def explain(request: PredictRequest) -> ExplainResponse:
    """Explain an applicant's risk score via SHAP (top risk / protective factors)."""
    try:
        service = get_model_service()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        result = service.explain(request.features)
    except Exception as exc:
        logger.exception("Explanation failed")
        raise HTTPException(status_code=500, detail=f"Explanation failed: {exc}") from exc

    return ExplainResponse(**result)
