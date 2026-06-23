from __future__ import annotations

import json
import logging
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import joblib
import pandas as pd

from backend.config import REPO_ROOT, settings

# Make the repository's `ml` package importable so we can reuse the SHAP logic
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.explain import build_explainer, explain_prediction, get_feature_names  # noqa: E402

logger = logging.getLogger(__name__)


class ModelService:
    """Loads the frozen production artifacts and serves predictions / explanations."""

    def __init__(self) -> None:
        self._validate_artifacts()

        self.model = joblib.load(settings.model_path)
        self.preprocessor = joblib.load(settings.preprocessor_path)
        logger.info("Loaded production model and preprocessor")

        with open(settings.metadata_path) as f:
            self.metadata: Dict = json.load(f)

        with open(settings.column_metadata_path) as f:
            col_meta = json.load(f)
        # Exact raw input columns the preprocessor was fitted on (order matters)
        self.expected_columns: List[str] = (
            col_meta["numerical_columns"] + col_meta["categorical_columns"]
        )

        # Reuse the project's SHAP machinery (native XGBoost pred_contribs explainer)
        self.feature_names = get_feature_names(self.preprocessor)
        self.explainer = build_explainer(self.model)
        logger.info(
            "ModelService ready — %d raw input columns, %d output features",
            len(self.expected_columns),
            len(self.feature_names),
        )

    @staticmethod
    def _validate_artifacts() -> None:
        for path in (
            settings.model_path,
            settings.preprocessor_path,
            settings.metadata_path,
            settings.column_metadata_path,
        ):
            if not path.exists():
                raise FileNotFoundError(
                    f"Missing production artifact: {path}. Run `python ml/freeze_production.py` first."
                )

    def _build_input_df(self, features: Dict) -> pd.DataFrame:
        """
        Build a single-row DataFrame with every column the preprocessor expects.
        Supplied features are used; missing ones become NaN (imputed downstream);
        unknown keys are ignored.
        """
        row = {col: features.get(col, None) for col in self.expected_columns}
        return pd.DataFrame([row], columns=self.expected_columns)

    def _risk_category(self, risk_score: float) -> str:
        if risk_score >= settings.high_risk_threshold:
            return "High Risk"
        if risk_score >= settings.medium_risk_threshold:
            return "Medium Risk"
        return "Low Risk"

    def predict(self, features: Dict) -> Dict:
        X = self._build_input_df(features)
        X_transformed = self.preprocessor.transform(X)
        probability = float(self.model.predict_proba(X_transformed)[0, 1])
        risk_score = round(probability * 100, 1)
        return {
            "risk_score": risk_score,
            "default_probability": round(probability, 4),
            "risk_category": self._risk_category(risk_score),
        }

    def embed(self, features: Dict) -> List[float]:
        """Return the model's preprocessed feature vector for an applicant (for similarity search)."""
        X = self._build_input_df(features)
        return self.preprocessor.transform(X)[0].astype(float).tolist()

    def similarity_drivers(
        self, query_emb: List[float], other_emb: List[float], top_n: int = 3
    ) -> List[str]:
        """
        Which features most drove the cosine similarity between two applicants.
        Per-dimension contribution to the dot product (q_i * m_i), aggregated to base
        features, ranked. Returns human-readable base-feature names.
        """
        import numpy as np

        from backend.services.llm_service import feature_base, humanize

        q = np.asarray(query_emb, dtype=float)
        m = np.asarray(other_emb, dtype=float)
        n = min(len(q), len(m), len(self.feature_names))
        if n == 0:
            return []
        contrib = q[:n] * m[:n]
        agg: Dict[str, float] = {}
        for i in range(n):
            base = feature_base(self.feature_names[i])
            agg[base] = agg.get(base, 0.0) + float(contrib[i])
        ranked = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
        drivers, seen = [], set()
        for base, score in ranked:
            if score <= 0:
                break
            label = humanize(base)
            if label not in seen:
                seen.add(label)
                drivers.append(label)
            if len(drivers) >= top_n:
                break
        return drivers

    def explain(self, features: Dict) -> Dict:
        X = self._build_input_df(features)
        # Reuse the shared explanation function with pre-loaded artifacts (no disk reload)
        return explain_prediction(
            X,
            model=self.model,
            preprocessor=self.preprocessor,
            explainer=self.explainer,
            feature_names=self.feature_names,
        )

    def model_info(self) -> Dict:
        return {
            "model_name": self.metadata.get("model_name", "XGBoost"),
            "model_version": self.metadata.get("model_version", "1.0.0"),
            "roc_auc": self.metadata.get("roc_auc"),
            "feature_count": self.metadata.get("feature_count"),
            "training_date": self.metadata.get("training_date"),
            "feature_sources": self.metadata.get("feature_sources", []),
        }


@lru_cache(maxsize=1)
def get_model_service() -> ModelService:
    """Lazily construct and cache a single ModelService instance."""
    return ModelService()
