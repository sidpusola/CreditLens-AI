from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)

RANDOM_STATE = 42


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_splits(
    data_dir: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    required = ["X_train.parquet", "X_test.parquet", "y_train.parquet", "y_test.parquet"]
    for name in required:
        if not (data_dir / name).exists():
            raise FileNotFoundError(
                f"Missing split file: {data_dir / name}. Run preprocess.py first."
            )

    X_train = pd.read_parquet(data_dir / "X_train.parquet")
    X_test = pd.read_parquet(data_dir / "X_test.parquet")
    # squeeze() converts single-column DataFrame back to Series
    y_train = pd.read_parquet(data_dir / "y_train.parquet").squeeze()
    y_test = pd.read_parquet(data_dir / "y_test.parquet").squeeze()

    logger.info("Loaded splits — train: %d samples, test: %d samples", len(X_train), len(X_test))
    return X_train, X_test, y_train, y_test


def load_preprocessor(models_dir: Path) -> ColumnTransformer:
    path = models_dir / "preprocessor.joblib"
    if not path.exists():
        raise FileNotFoundError(
            f"Preprocessor not found at {path}. Run preprocess.py first."
        )
    preprocessor = joblib.load(path)
    logger.info("Loaded preprocessor from %s", path)
    return preprocessor


def transform_splits(
    preprocessor: ColumnTransformer,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray]:
    X_train_t = preprocessor.transform(X_train)
    X_test_t = preprocessor.transform(X_test)
    logger.info("Transformed features — output shape: %s", X_train_t.shape)
    return X_train_t, X_test_t


def build_models(scale_pos_weight: float) -> Dict[str, Any]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            solver="lbfgs",
            random_state=RANDOM_STATE,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight="balanced",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
        "xgboost": XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            eval_metric="auc",
            verbosity=0,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
    }


def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: pd.Series,
) -> Dict[str, float]:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
    }


def train_and_evaluate(
    models: Dict[str, Any],
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: pd.Series,
    y_test: pd.Series,
) -> Dict[str, Dict[str, float]]:
    results: Dict[str, Dict[str, float]] = {}

    for name, model in models.items():
        logger.info("Training %s ...", name)
        model.fit(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        results[name] = metrics
        logger.info("%s — %s", name, metrics)

    return results


def recommend_best_model(results: Dict[str, Dict[str, float]]) -> str:
    # ROC-AUC is primary for imbalanced binary classification
    return max(results, key=lambda name: results[name]["roc_auc"])


def get_feature_names(preprocessor: ColumnTransformer) -> List[str]:
    return list(preprocessor.get_feature_names_out())


def build_feature_importance(
    model: XGBClassifier,
    feature_names: List[str],
    top_n: int = 30,
) -> pd.DataFrame:
    importances = model.feature_importances_
    df = (
        pd.DataFrame({"feature": feature_names, "importance": importances})
        .sort_values("importance", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    df.insert(0, "rank", df.index + 1)
    return df


def save_feature_importance(importance_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    importance_df.to_csv(output_path, index=False)
    logger.info("XGBoost feature importance saved to %s", output_path)


def load_results_for_tag(
    models_dir: Path, tag: str
) -> Optional[Dict[str, Dict[str, float]]]:
    path = models_dir / f"model_comparison_{tag}.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    return data.get("results")


def load_baseline_results(models_dir: Path) -> Optional[Dict[str, Dict[str, float]]]:
    return load_results_for_tag(models_dir, "baseline")


def save_models(models: Dict[str, Any], models_dir: Path) -> None:
    for name, model in models.items():
        path = models_dir / f"{name}.joblib"
        joblib.dump(model, path)
        logger.info("Saved %s to %s", name, path)


def save_comparison(
    results: Dict[str, Dict[str, float]],
    best_model_name: str,
    models_dir: Path,
    tag: str,
) -> None:
    output_path = models_dir / f"model_comparison_{tag}.json"
    output = {
        "results": results,
        "best_model": best_model_name,
        "primary_metric": "roc_auc",
        "tag": tag,
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    logger.info("Model comparison saved to %s", output_path)


# Ordered progression of feature-set milestones for the markdown report
PROGRESSION_TAGS = [
    "baseline",
    "bureau",
    "prev_app",
    "installments",
    "credit_card",
    "pos_cash",
    "bureau_balance",
]
TAG_LABELS = {
    "baseline": "Baseline (application_train)",
    "bureau": "+ bureau",
    "prev_app": "+ previous_application",
    "installments": "+ installments_payments",
    "credit_card": "+ credit_card_balance",
    "pos_cash": "+ POS_CASH_balance",
    "bureau_balance": "+ bureau_balance",
}


def build_markdown_report(
    results: Dict[str, Dict[str, float]],
    best_model_name: str,
    models_dir: Path,
    tag: str,
) -> str:
    lines: List[str] = []
    lines.append("# CreditLens AI - Model Comparison Report")
    lines.append("")
    lines.append(f"**Feature set:** `{tag}`  ")
    lines.append(f"**Primary metric:** ROC-AUC (imbalanced ~8% default rate)  ")
    lines.append(f"**Best model:** {MODEL_DISPLAY_NAMES.get(best_model_name, best_model_name)}")
    lines.append("")

    # Current run - full metrics for all models
    lines.append(f"## Current run: `{tag}`")
    lines.append("")
    lines.append("| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |")
    lines.append("|---|---|---|---|---|---|")
    for name, scores in results.items():
        display = MODEL_DISPLAY_NAMES.get(name, name)
        if name == best_model_name:
            display += " *"
        lines.append(
            f"| {display} | {scores['accuracy']:.4f} | {scores['precision']:.4f} | "
            f"{scores['recall']:.4f} | {scores['f1']:.4f} | {scores['roc_auc']:.4f} |"
        )
    lines.append("")

    # XGBoost ROC-AUC progression across feature-set milestones
    lines.append("## XGBoost ROC-AUC progression")
    lines.append("")
    lines.append("| Feature set | ROC-AUC | Delta vs baseline |")
    lines.append("|---|---|---|")
    baseline_auc: Optional[float] = None
    for ptag in PROGRESSION_TAGS:
        if ptag == tag:
            tag_results = results
        else:
            tag_results = load_results_for_tag(models_dir, ptag)
        if not tag_results or "xgboost" not in tag_results:
            continue
        auc = tag_results["xgboost"]["roc_auc"]
        if ptag == "baseline":
            baseline_auc = auc
        delta = "-" if baseline_auc is None else f"{auc - baseline_auc:+.4f}"
        label = TAG_LABELS.get(ptag, ptag)
        lines.append(f"| {label} | {auc:.4f} | {delta} |")
    lines.append("")

    return "\n".join(lines)


def save_report(
    results: Dict[str, Dict[str, float]],
    best_model_name: str,
    models_dir: Path,
    report_dir: Path,
    tag: str,
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / "model_comparison.json"
    with open(json_path, "w") as f:
        json.dump(
            {
                "results": results,
                "best_model": best_model_name,
                "primary_metric": "roc_auc",
                "tag": tag,
            },
            f,
            indent=2,
        )
    logger.info("Report JSON saved to %s", json_path)

    md = build_markdown_report(results, best_model_name, models_dir, tag)
    md_path = report_dir / "model_comparison.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    logger.info("Report Markdown saved to %s", md_path)


MODEL_DISPLAY_NAMES: Dict[str, str] = {
    "logistic_regression": "Logistic Regression",
    "random_forest": "Random Forest",
    "xgboost": "XGBoost",
}

METRIC_DISPLAY_NAMES: Dict[str, str] = {
    "accuracy": "Accuracy",
    "precision": "Precision",
    "recall": "Recall",
    "f1": "F1",
    "roc_auc": "ROC-AUC",
}


def print_report(
    results: Dict[str, Dict[str, float]],
    best_model_name: str,
) -> None:
    rows = []
    for name, scores in results.items():
        display_name = MODEL_DISPLAY_NAMES.get(name, name)
        if name == best_model_name:
            display_name += " *"
        row: Dict[str, Any] = {"Model": display_name}
        row.update({METRIC_DISPLAY_NAMES[k]: v for k, v in scores.items()})
        rows.append(row)

    df = pd.DataFrame(rows).set_index("Model")
    print(df.to_string(float_format=lambda x: f"{x:.4f}"))
    print()
    best_display = MODEL_DISPLAY_NAMES.get(best_model_name, best_model_name)
    print(f"  * Recommended model : {best_display}")
    print(f"    Primary metric    : ROC-AUC")
    print(f"    Reason            : Imbalanced dataset (~8% default rate).")
    print(f"                        ROC-AUC is not inflated by the majority class.")
    print()


def print_delta(
    results: Dict[str, Dict[str, float]],
    baseline_results: Dict[str, Dict[str, float]],
) -> None:
    delta_rows = []
    for name, scores in results.items():
        if name not in baseline_results:
            continue
        display_name = MODEL_DISPLAY_NAMES.get(name, name)
        row: Dict[str, Any] = {"Model": display_name}
        row.update(
            {
                METRIC_DISPLAY_NAMES[k]: scores[k] - baseline_results[name][k]
                for k in scores
                if k in baseline_results[name]
            }
        )
        delta_rows.append(row)

    if not delta_rows:
        return

    df = pd.DataFrame(delta_rows).set_index("Model")
    print("--- Delta vs Baseline (Bureau - Baseline) ---\n")
    print(df.to_string(float_format=lambda x: f"{x:+.4f}"))
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CreditLens AI: Train and evaluate models"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory containing train/test parquet splits from preprocess.py",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=Path("models"),
        help="Directory to load preprocessor from and save trained models to",
    )
    parser.add_argument(
        "--results-tag",
        type=str,
        default="baseline",
        help="Tag for output files, e.g. 'baseline', 'bureau', 'prev_app' (default: baseline)",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=None,
        help=(
            "Optional directory to also write model_comparison.json and "
            "model_comparison.md (e.g. reports/previous_application)"
        ),
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    X_train, X_test, y_train, y_test = load_splits(args.data_dir)
    preprocessor = load_preprocessor(args.models_dir)
    X_train_t, X_test_t = transform_splits(preprocessor, X_train, X_test)

    # Ratio of negative to positive samples — corrects for class imbalance in XGBoost
    scale_pos_weight = float((y_train == 0).sum() / (y_train == 1).sum())
    logger.info("Class imbalance ratio (scale_pos_weight): %.2f", scale_pos_weight)

    models = build_models(scale_pos_weight)
    results = train_and_evaluate(models, X_train_t, X_test_t, y_train, y_test)

    save_models(models, args.models_dir)
    best_model_name = recommend_best_model(results)
    save_comparison(results, best_model_name, args.models_dir, args.results_tag)

    # Save XGBoost feature importances
    feature_names = get_feature_names(preprocessor)
    xgb_model = models["xgboost"]
    importance_df = build_feature_importance(xgb_model, feature_names)
    save_feature_importance(
        importance_df,
        args.models_dir / f"xgboost_feature_importance_{args.results_tag}.csv",
    )

    print(f"\n=== CreditLens AI — Model Comparison [{args.results_tag}] ===\n")
    print_report(results, best_model_name)

    # Show delta if a baseline exists and this run is not the baseline
    if args.results_tag != "baseline":
        baseline = load_baseline_results(args.models_dir)
        if baseline:
            print_delta(results, baseline)

    # Optionally write a clean JSON + Markdown report (e.g. reports/credit_card_balance)
    if args.report_dir is not None:
        save_feature_importance(importance_df, args.report_dir / "feature_importance.csv")
        save_report(
            results,
            best_model_name,
            args.models_dir,
            args.report_dir,
            args.results_tag,
        )


if __name__ == "__main__":
    main()
