from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Factor(BaseModel):
    feature: str = Field(..., description="Feature name.")
    impact: float = Field(..., description="SHAP impact; positive = pushes toward default.")


class ExplainResponse(BaseModel):
    risk_score: float = Field(..., description="Default risk on a 0-100 scale.")
    top_risk_factors: List[Factor] = Field(
        ..., description="Features pushing the prediction toward default."
    )
    top_protective_factors: List[Factor] = Field(
        ..., description="Features pulling the prediction away from default."
    )


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    roc_auc: float
    feature_count: int
    training_date: str
    feature_sources: List[str]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    persistence_enabled: bool = False
