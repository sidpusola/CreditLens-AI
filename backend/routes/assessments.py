from __future__ import annotations

import logging

import datetime as dt

from fastapi import APIRouter, HTTPException, Query

from backend.config import settings
from backend.schemas.assessment import (
    DECISIONS,
    AssessmentListResponse,
    AssessmentRecord,
    CreateAssessmentRequest,
    DecisionRequest,
    SimilarApplicant,
    SimilarResponse,
)
from backend.schemas.prediction import PredictRequest
from backend.services.model_service import get_model_service
from backend.services.supabase_service import SupabaseNotConfigured, get_supabase_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["assessments"])


def _confidence(probability: float) -> float:
    # Distance from the 0.5 decision boundary, as a 0-100 score
    return round(abs(probability - 0.5) * 2 * 100, 1)


@router.post("/assessments", response_model=AssessmentRecord, status_code=201)
def create_assessment(request: CreateAssessmentRequest) -> AssessmentRecord:
    """Score an applicant, then persist the full assessment (+ case metadata) to Supabase."""
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
        "case_meta": request.case.model_dump(exclude_none=True) if request.case else {},
    }

    # Embed the applicant for similarity search (only when pgvector is enabled)
    embedding = None
    if settings.vector_search_enabled:
        try:
            embedding = model.embed(request.features)
        except Exception:
            logger.exception("Embedding failed; saving without it")

    try:
        saved = supabase.save_assessment(record, embedding=embedding)
    except SupabaseNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Supabase save failed")
        raise HTTPException(status_code=502, detail=f"Could not persist assessment: {exc}") from exc

    return AssessmentRecord(**saved)


@router.post("/assessments/similar", response_model=SimilarResponse)
def similar_assessments(
    request: PredictRequest, limit: int = Query(5, ge=1, le=20)
) -> SimilarResponse:
    """Find the most similar historical applicants (pgvector cosine nearest neighbours)."""
    if not settings.vector_search_enabled:
        raise HTTPException(
            status_code=503,
            detail="Vector search is disabled. Run backend/db/pgvector.sql and set ENABLE_VECTOR_SEARCH=true.",
        )

    model = get_model_service()
    supabase = get_supabase_service()
    try:
        embedding = model.embed(request.features)
        rows = supabase.match_assessments(embedding, match_count=limit)
    except SupabaseNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Similarity search failed")
        raise HTTPException(status_code=502, detail=f"Similarity search failed: {exc}") from exc

    return SimilarResponse(count=len(rows), items=[SimilarApplicant(**r) for r in rows])


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


@router.patch("/assessments/{assessment_id}/decision", response_model=AssessmentRecord)
def record_decision(assessment_id: str, request: DecisionRequest) -> AssessmentRecord:
    """Record the loan officer's decision on a persisted assessment."""
    if request.decision not in DECISIONS:
        raise HTTPException(status_code=422, detail=f"decision must be one of {DECISIONS}")

    supabase = get_supabase_service()
    fields = {
        "decision": request.decision,
        "decision_note": request.note,
        "decided_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    try:
        updated = supabase.update_assessment(assessment_id, fields)
    except SupabaseNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Decision update failed")
        raise HTTPException(status_code=502, detail=f"Could not record decision: {exc}") from exc

    if updated is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentRecord(**updated)


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
