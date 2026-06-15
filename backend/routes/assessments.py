from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from backend.schemas.assessment import AssessmentListResponse, AssessmentRecord
from backend.schemas.prediction import PredictRequest
from backend.services.model_service import get_model_service
from backend.services.supabase_service import SupabaseNotConfigured, get_supabase_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["assessments"])


def _confidence(probability: float) -> float:
    # Distance from the 0.5 decision boundary, as a 0-100 score
    return round(abs(probability - 0.5) * 2 * 100, 1)


@router.post("/assessments", response_model=AssessmentRecord, status_code=201)
def create_assessment(request: PredictRequest) -> AssessmentRecord:
    """Score an applicant, then persist the full assessment to Supabase."""
    model = get_model_service()
    supabase = get_supabase_service()

    try:
        prediction = model.predict(request.features)
        explanation = model.explain(request.features)
    except Exception as exc:
        logger.exception("Scoring failed")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {exc}") from exc

    record = {
        "risk_score": prediction["risk_score"],
        "default_probability": prediction["default_probability"],
        "risk_category": prediction["risk_category"],
        "confidence": _confidence(prediction["default_probability"]),
        "top_risk_factors": explanation["top_risk_factors"],
        "top_protective_factors": explanation["top_protective_factors"],
        "inputs": request.features,
    }

    try:
        saved = supabase.save_assessment(record)
    except SupabaseNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Supabase save failed")
        raise HTTPException(status_code=502, detail=f"Could not persist assessment: {exc}") from exc

    return AssessmentRecord(**saved)


@router.get("/assessments", response_model=AssessmentListResponse)
def list_assessments(limit: int = Query(25, ge=1, le=100)) -> AssessmentListResponse:
    """List recent persisted assessments (most recent first)."""
    supabase = get_supabase_service()
    try:
        rows = supabase.list_assessments(limit=limit)
    except SupabaseNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Supabase list failed")
        raise HTTPException(status_code=502, detail=f"Could not list assessments: {exc}") from exc

    return AssessmentListResponse(count=len(rows), items=[AssessmentRecord(**r) for r in rows])


@router.get("/assessments/{assessment_id}", response_model=AssessmentRecord)
def get_assessment(assessment_id: str) -> AssessmentRecord:
    """Fetch a single persisted assessment by id."""
    supabase = get_supabase_service()
    try:
        row = supabase.get_assessment(assessment_id)
    except SupabaseNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Supabase fetch failed")
        raise HTTPException(status_code=502, detail=f"Could not fetch assessment: {exc}") from exc

    if row is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentRecord(**row)
