from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from backend.schemas.explanation import Factor


# Allowed officer decisions
DECISIONS = ["Approved", "Manual Review", "Rejected", "Documents Requested"]


class CaseMeta(BaseModel):
    """Case-file metadata about the applicant (not model features)."""

    applicant_id: Optional[str] = None
    applicant_name: Optional[str] = None
    loan_amount: Optional[float] = None
    loan_purpose: Optional[str] = None
    application_date: Optional[str] = None
    officer_name: Optional[str] = None


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
    case_meta: dict = Field(default_factory=dict)
    decision: Optional[str] = None
    decision_note: Optional[str] = None
    decided_at: Optional[str] = None


class CreateAssessmentRequest(BaseModel):
    features: dict = Field(default_factory=dict)
    case: Optional[CaseMeta] = None


class DecisionRequest(BaseModel):
    decision: str = Field(..., description="One of: Approved, Manual Review, Rejected, Documents Requested")
    note: Optional[str] = Field(None, description="Optional officer note.")


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
    case_id: Optional[str] = None
    decision: Optional[str] = None
    outcome: Optional[str] = Field(None, description="Actual repayment outcome if known (Defaulted/Repaid).")
    similarity_drivers: List[str] = Field(default_factory=list)


class SimilarResponse(BaseModel):
    count: int
    items: List[SimilarApplicant]


class ReportResponse(BaseModel):
    report: str = Field(..., description="LLM-generated underwriting narrative.")
    model: str = Field(..., description="LLM that produced the report.")
    risk_score: float
    risk_category: str
    similar_used: int = Field(..., description="Number of retrieved precedent cases used (RAG).")
