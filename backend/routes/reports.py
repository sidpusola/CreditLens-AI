from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from backend.config import settings
from backend.schemas.assessment import ReportResponse
from backend.schemas.prediction import PredictRequest
from backend.services.llm_service import LLMUnavailable, get_llm_service
from backend.services.model_service import get_model_service
from backend.services.supabase_service import get_supabase_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reports"])


@router.post("/report", response_model=ReportResponse)
def generate_report(request: PredictRequest, similar_count: int = Query(5, ge=0, le=10)) -> ReportResponse:
    """
    RAG underwriting report: score the applicant, retrieve similar precedent cases
    (pgvector), and have the local LLM write a grounded narrative.
    """
    model = get_model_service()
    llm = get_llm_service()

    try:
        prediction = model.predict(request.features)
        explanation = model.explain(request.features)
    except Exception as exc:
        logger.exception("Scoring failed")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {exc}") from exc

    # RAG retrieval — nearest historical applicants (best-effort; skipped if vector search is off)
    similar = []
    if settings.vector_search_enabled and similar_count > 0:
        try:
            embedding = model.embed(request.features)
            similar = get_supabase_service().match_assessments(embedding, match_count=similar_count)
        except Exception:
            logger.exception("Similarity retrieval failed; generating report without precedent")

    try:
        report = llm.generate_report(prediction, explanation, request.features, similar)
    except LLMUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Report generation failed")
        raise HTTPException(status_code=502, detail=f"Report generation failed: {exc}") from exc

    return ReportResponse(
        report=report,
        model=llm.model,
        risk_score=prediction["risk_score"],
        risk_category=prediction["risk_category"],
        similar_used=len(similar),
    )
