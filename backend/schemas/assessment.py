from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from backend.schemas.explanation import Factor


class AssessmentRecord(BaseModel):
    """A persisted assessment as returned by the database."""

    id: str
    created_at: Optional[str] = None
    risk_score: float
    default_probability: float
    risk_category: str
    confidence: Optional[float] = None
    top_risk_factors: List[Factor] = Field(default_factory=list)
    top_protective_factors: List[Factor] = Field(default_factory=list)
    inputs: dict = Field(default_factory=dict)


class AssessmentListResponse(BaseModel):
    count: int
    items: List[AssessmentRecord]


class SimilarApplicant(BaseModel):
    id: str
    created_at: Optional[str] = None
    risk_score: float
    default_probability: float
    risk_category: str
    similarity: float = Field(..., description="Cosine similarity (1.0 = identical).")


class SimilarResponse(BaseModel):
    count: int
    items: List[SimilarApplicant]


class ReportResponse(BaseModel):
    report: str = Field(..., description="LLM-generated underwriting narrative.")
    model: str = Field(..., description="LLM that produced the report.")
    risk_score: float
    risk_category: str
    similar_used: int = Field(..., description="Number of retrieved precedent cases used (RAG).")
