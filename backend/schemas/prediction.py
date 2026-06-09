from __future__ import annotations

from typing import Dict, Optional, Union

from pydantic import BaseModel, Field

# A single applicant feature value may be numeric, categorical (str), or missing (null)
FeatureValue = Optional[Union[float, int, str]]


class PredictRequest(BaseModel):
    """
    Flexible applicant payload. Send any subset of the model's raw input columns;
    omitted columns are imputed by the preprocessing pipeline (median / most-frequent).
    """

    features: Dict[str, FeatureValue] = Field(
        ...,
        description="Mapping of feature name to value (numeric, string, or null).",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "features": {
                    "EXT_SOURCE_2": 0.21,
                    "EXT_SOURCE_3": 0.18,
                    "AMT_CREDIT": 450000,
                    "AMT_ANNUITY": 24700,
                    "DAYS_BIRTH": -12000,
                    "late_payment_ratio": 0.42,
                    "NAME_CONTRACT_TYPE": "Cash loans",
                }
            }
        }
    }


class PredictResponse(BaseModel):
    risk_score: float = Field(..., description="Default risk on a 0-100 scale.")
    default_probability: float = Field(..., description="Model probability of default (0-1).")
    risk_category: str = Field(..., description="Low Risk / Medium Risk / High Risk.")
