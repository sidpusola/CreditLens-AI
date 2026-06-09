from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must be set before pyplot import
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)

GLOBAL_SAMPLE_SIZE = 5000   # rows sampled from X_test for global SHAP (speed/memory)
TOP_FEATURES = 20            # features shown in global importance plot and CSV
TOP_FACTORS = 5              # risk/protective factors shown in local explanation
RANDOM_STATE = 42


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


# ---------------------------------------------------------------------------
# Artifact loaders
# ---------------------------------------------------------------------------

def load_model(models_dir: Path) -> XGBClassifier:
    path = models_dir / "xgboost.joblib"
    if not path.exists():
        raise FileNotFoundError(f"Model not found at {path}. Run train_baseline.py first.")
    model = joblib.load(path)
    logger.info("Loaded XGBoost model from %s", path)
    return model


def load_preprocessor(models_dir: Path) -> ColumnTransformer:
    path = models_dir / "preprocessor.joblib"
    if not path.exists():
        raise FileNotFoundError(f"Preprocessor not found at {path}. Run preprocess.py first.")
    preprocessor = joblib.load(path)
    logger.info("Loaded preprocessor from %s", path)
    return preprocessor


def load_splits(
    data_dir: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    for name in ("X_train.parquet", "X_test.parquet", "y_test.parquet"):
        if not (data_dir / name).exists():
            raise FileNotFoundError(
                f"Missing file: {data_dir / name}. Run preprocess.py first."
            )
    X_train = pd.read_parquet(data_dir / "X_train.parquet")
    X_test = pd.read_parquet(data_dir / "X_test.parquet")
    y_test = pd.read_parquet(data_dir / "y_test.parquet").squeeze()
    logger.info("Loaded splits — train: %d, test: %d", len(X_train), len(X_test))
    return X_train, X_test, y_test


# ---------------------------------------------------------------------------
# Feature name extraction
# ---------------------------------------------------------------------------

def get_feature_names(preprocessor: ColumnTransformer) -> List[str]:
    """
    Extracts output feature names from the fitted ColumnTransformer.
    Numerical columns keep their original names.
    Categorical OHE columns become e.g. 'NAME_CONTRACT_TYPE_Cash loans'.
    """
    feature_names = list(preprocessor.get_feature_names_out())
    logger.info("Extracted %d feature names from preprocessor", len(feature_names))
    return feature_names


# ---------------------------------------------------------------------------
# SHAP core
# ---------------------------------------------------------------------------

class NativeXGBExplainer:
    """
    Uses XGBoost's built-in pred_contribs instead of shap.TreeExplainer.
    Avoids SHAP/XGBoost version coupling (shap 0.49 crashes on XGBoost 3.x base_score format).
    The interface mirrors TreeExplainer.shap_values() so the rest of the code is unchanged.
    """

    def __init__(self, model: XGBClassifier) -> None:
        self._booster = model.get_booster()

    def shap_values(self, X: np.ndarray) -> np.ndarray:
        dmatrix = xgb.DMatrix(X)
        # pred_contribs returns (n_samples, n_features + 1); last col is the bias term
        contribs = self._booster.predict(dmatrix, pred_contribs=True)
        return contribs[:, :-1]


def build_explainer(model: XGBClassifier) -> NativeXGBExplainer:
    explainer = NativeXGBExplainer(model)
    logger.info("NativeXGBExplainer built (XGBoost pred_contribs)")
    return explainer


def compute_shap_values(
    explainer: Any,
    X_transformed: np.ndarray,
) -> np.ndarray:
    logger.info("Computing SHAP values for %d samples ...", X_transformed.shape[0])
    shap_vals = explainer.shap_values(X_transformed)
    # NativeXGBExplainer already returns a plain array; guard for old shap.TreeExplainer
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]
    logger.info("SHAP values computed — shape: %s", shap_vals.shape)
    return shap_vals


# ---------------------------------------------------------------------------
# Global analysis
# ---------------------------------------------------------------------------

def get_global_importance(
    shap_values: np.ndarray,
    feature_names: List[str],
    top_n: int = TOP_FEATURES,
) -> pd.DataFrame:
    mean_abs = np.abs(shap_values).mean(axis=0)
    df = (
        pd.DataFrame({"feature": feature_names, "mean_abs_shap": mean_abs})
        .sort_values("mean_abs_shap", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    df.insert(0, "rank", df.index + 1)
    return df


def plot_summary_bar(
    shap_values: np.ndarray,
    X_transformed: np.ndarray,
    feature_names: List[str],
    output_path: Path,
    top_n: int = TOP_FEATURES,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 8))
    shap.summary_plot(
        shap_values,
        X_transformed,
        feature_names=feature_names,
        plot_type="bar",
        max_display=top_n,
        show=False,
    )
    plt.title("Top 20 Features — Mean |SHAP Value|", fontsize=13, pad=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("SHAP summary bar plot saved to %s", output_path)


# ---------------------------------------------------------------------------
# Local explanation
# ---------------------------------------------------------------------------

def explain_single_prediction(
    input_df: pd.DataFrame,
    model: XGBClassifier,
    preprocessor: ColumnTransformer,
    explainer: Any,
    feature_names: List[str],
    top_n: int = TOP_FACTORS,
) -> Dict:
    X_transformed = preprocessor.transform(input_df)

    prob = float(model.predict_proba(X_transformed)[0, 1])
    risk_score = round(prob * 100, 1)

    shap_vals = explainer.shap_values(X_transformed)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]
    shap_row = shap_vals[0]

    # Sort features by SHAP value descending (most positive first)
    feature_shap = sorted(
        zip(feature_names, shap_row.tolist()),
        key=lambda x: x[1],
        reverse=True,
    )

    # Positive SHAP → pushes toward default (risk factor)
    top_risk_factors = [
        {"feature": f, "impact": round(v, 4)}
        for f, v in feature_shap
        if v > 0
    ][:top_n]

    # Negative SHAP → pulls away from default (protective factor)
    # reversed(feature_shap) starts from the most negative end
    top_protective_factors = [
        {"feature": f, "impact": round(v, 4)}
        for f, v in reversed(feature_shap)
        if v < 0
    ][:top_n]

    return {
        "risk_score": risk_score,
        "top_risk_factors": top_risk_factors,
        "top_protective_factors": top_protective_factors,
    }


# ---------------------------------------------------------------------------
# Public reusable API — used by Phase 6 (FastAPI) and Phase 7 (Streamlit)
# ---------------------------------------------------------------------------

def explain_prediction(
    input_df: pd.DataFrame,
    model: Optional[XGBClassifier] = None,
    preprocessor: Optional[ColumnTransformer] = None,
    explainer: Optional[Any] = None,
    feature_names: Optional[List[str]] = None,
    models_dir: Path = Path("models"),
) -> Dict:
    """
    Explain a single applicant's default risk prediction.

    Standalone usage (loads artifacts from disk):
        result = explain_prediction(applicant_df)

    Efficient usage for repeated calls (pass pre-loaded artifacts):
        result = explain_prediction(applicant_df, model=model,
                                    preprocessor=preprocessor,
                                    explainer=explainer,
                                    feature_names=feature_names)

    Returns:
        {
            "risk_score": float (0–100),
            "top_risk_factors": [{"feature": str, "impact": float}, ...],
            "top_protective_factors": [{"feature": str, "impact": float}, ...]
        }
    """
    if model is None:
        model = load_model(models_dir)
    if preprocessor is None:
        preprocessor = load_preprocessor(models_dir)
    if feature_names is None:
        feature_names = get_feature_names(preprocessor)
    if explainer is None:
        explainer = build_explainer(model)

    return explain_single_prediction(
        input_df, model, preprocessor, explainer, feature_names
    )


# ---------------------------------------------------------------------------
# Output persistence
# ---------------------------------------------------------------------------

def save_outputs(
    importance_df: pd.DataFrame,
    local_explanation: Dict,
    reports_dir: Path,
) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)

    csv_path = reports_dir / "shap_feature_importance.csv"
    importance_df.to_csv(csv_path, index=False)
    logger.info("Feature importance CSV saved to %s", csv_path)

    json_path = reports_dir / "local_explanation_sample.json"
    with open(json_path, "w") as f:
        json.dump(local_explanation, f, indent=2)
    logger.info("Local explanation JSON saved to %s", json_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CreditLens AI Phase 5: SHAP Explainability"
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--models-dir", type=Path, default=Path("models"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/shap"))
    parser.add_argument(
        "--sample-index",
        type=int,
        default=0,
        help="Index of the test sample to explain locally (default: 0)",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    # Load artifacts
    model = load_model(args.models_dir)
    preprocessor = load_preprocessor(args.models_dir)
    feature_names = get_feature_names(preprocessor)
    _, X_test, _ = load_splits(args.data_dir)

    # Transform full test set
    X_test_t = preprocessor.transform(X_test)

    # Sample for global SHAP to control memory and runtime
    rng = np.random.default_rng(RANDOM_STATE)
    idx = rng.choice(
        len(X_test_t),
        size=min(GLOBAL_SAMPLE_SIZE, len(X_test_t)),
        replace=False,
    )
    X_global = X_test_t[idx]

    # Build explainer once — reused for global and local
    explainer = build_explainer(model)

    # --- Global analysis ---
    shap_values = compute_shap_values(explainer, X_global)
    importance_df = get_global_importance(shap_values, feature_names, top_n=TOP_FEATURES)
    plot_summary_bar(
        shap_values, X_global, feature_names,
        args.reports_dir / "shap_summary_bar.png",
    )
    logger.info(
        "Top 10 features by mean |SHAP|:\n%s",
        importance_df.head(10).to_string(index=False),
    )

    # --- Local analysis ---
    sample_row = X_test.iloc[[args.sample_index]]
    local_explanation = explain_prediction(
        sample_row,
        model=model,
        preprocessor=preprocessor,
        explainer=explainer,
        feature_names=feature_names,
    )

    # --- Save outputs ---
    save_outputs(importance_df, local_explanation, args.reports_dir)

    # --- Print local explanation ---
    print(
        f"\n=== CreditLens AI Phase 5 — Local Explanation "
        f"(Test Sample Index: {args.sample_index}) ===\n"
    )
    print(json.dumps(local_explanation, indent=2))
    print()


if __name__ == "__main__":
    main()
