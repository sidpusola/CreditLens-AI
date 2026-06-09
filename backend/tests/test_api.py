from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.config import REPO_ROOT

client = TestClient(app)


@pytest.fixture(scope="module")
def sample_features() -> dict:
    """A realistic applicant: the first row of the held-out test set as a feature dict."""
    x_test_path = REPO_ROOT / "data" / "processed" / "X_test.parquet"
    if not x_test_path.exists():
        pytest.skip("X_test.parquet not found; run preprocess.py first")
    row = pd.read_parquet(x_test_path).iloc[0].to_dict()
    # JSON cannot represent NaN — convert to None (the API imputes missing values)
    return {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items()}


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["endpoints"] == ["/health", "/predict", "/explain", "/model-info"]


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_model_info():
    resp = client.get("/model-info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_name"] == "XGBoost"
    assert 0.5 < body["roc_auc"] < 1.0
    assert body["feature_count"] > 0
    assert "POS_CASH_balance" in body["feature_sources"]


def test_predict_full(sample_features):
    resp = client.post("/predict", json={"features": sample_features})
    assert resp.status_code == 200
    body = resp.json()
    assert 0.0 <= body["risk_score"] <= 100.0
    assert 0.0 <= body["default_probability"] <= 1.0
    assert body["risk_category"] in {"Low Risk", "Medium Risk", "High Risk"}
    # risk_score should be probability * 100
    assert abs(body["risk_score"] - body["default_probability"] * 100) < 0.1


def test_predict_empty():
    """An empty payload is valid — every feature is imputed."""
    resp = client.post("/predict", json={"features": {}})
    assert resp.status_code == 200
    assert 0.0 <= resp.json()["default_probability"] <= 1.0


def test_explain(sample_features):
    resp = client.post("/explain", json={"features": sample_features})
    assert resp.status_code == 200
    body = resp.json()
    assert "risk_score" in body
    assert isinstance(body["top_risk_factors"], list)
    assert isinstance(body["top_protective_factors"], list)
    assert len(body["top_risk_factors"]) > 0
    factor = body["top_risk_factors"][0]
    assert "feature" in factor and "impact" in factor
    # Risk factors push toward default (positive), protective pull away (negative)
    assert factor["impact"] > 0
    assert body["top_protective_factors"][0]["impact"] < 0


def test_predict_validation_error():
    """`features` must be an object, not a list — expect a 422."""
    resp = client.post("/predict", json={"features": [1, 2, 3]})
    assert resp.status_code == 422
