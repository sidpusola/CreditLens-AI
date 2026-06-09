from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import shutil
from pathlib import Path

import joblib

logger = logging.getLogger(__name__)

# The feature sources kept in the production model (bureau_balance was discarded)
PRODUCTION_SOURCES = [
    "application_train",
    "bureau",
    "previous_application",
    "installments_payments",
    "credit_card_balance",
    "POS_CASH_balance",
]


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def freeze(models_dir: Path, output_dir: Path, roc_auc: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy the frozen artifacts under stable production names
    artifacts = {
        "xgboost.joblib": "xgboost_production.joblib",
        "preprocessor.joblib": "preprocessor_production.joblib",
        "column_metadata.json": "column_metadata.json",
    }
    for src_name, dst_name in artifacts.items():
        src = models_dir / src_name
        if not src.exists():
            raise FileNotFoundError(f"Missing artifact {src}. Run preprocess.py + train_baseline.py first.")
        shutil.copy2(src, output_dir / dst_name)
        logger.info("Froze %s -> %s", src, output_dir / dst_name)

    # Derive the output feature count from the fitted preprocessor
    preprocessor = joblib.load(output_dir / "preprocessor_production.joblib")
    feature_count = int(len(preprocessor.get_feature_names_out()))

    metadata = {
        "model_name": "XGBoost",
        "model_version": "1.0.0",
        "roc_auc": roc_auc,
        "feature_count": feature_count,
        "training_date": dt.date.today().isoformat(),
        "feature_sources": PRODUCTION_SOURCES,
        "primary_metric": "roc_auc",
        "notes": "bureau_balance excluded (redundant, regressed AUC).",
    }
    with open(output_dir / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Wrote model metadata to %s", output_dir / "model_metadata.json")
    logger.info("Production feature count: %d", feature_count)


def read_roc_auc(models_dir: Path, tag: str) -> float:
    path = models_dir / f"model_comparison_{tag}.json"
    if not path.exists():
        raise FileNotFoundError(f"Comparison file not found: {path}")
    with open(path) as f:
        data = json.load(f)
    return float(data["results"]["xgboost"]["roc_auc"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze the current best model into production artifacts for the API"
    )
    parser.add_argument("--models-dir", type=Path, default=Path("models"))
    parser.add_argument("--output-dir", type=Path, default=Path("backend/models"))
    parser.add_argument(
        "--results-tag",
        type=str,
        default="pos_cash",
        help="Comparison tag to read ROC-AUC from (default: pos_cash, the best config)",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()
    roc_auc = read_roc_auc(args.models_dir, args.results_tag)
    freeze(args.models_dir, args.output_dir, roc_auc)
    print(f"\nProduction artifacts frozen to {args.output_dir} (ROC-AUC {roc_auc}).\n")


if __name__ == "__main__":
    main()
