from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

ID_COLUMN = "SK_ID_CURR"
STATUS_COL = "NAME_CONTRACT_STATUS"
CONTRACT_TYPE_COL = "NAME_CONTRACT_TYPE"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_previous_application(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"previous_application.csv not found at {path}")
    df = pd.read_csv(path)
    logger.info("Loaded previous_application: %d rows, %d columns", *df.shape)
    return df


def _count_by_value(
    prev: pd.DataFrame,
    column: str,
    value: str,
    feature_name: str,
) -> pd.Series:
    """Count rows per applicant where `column` equals `value`."""
    return (
        prev[prev[column] == value]
        .groupby(ID_COLUMN)
        .size()
        .rename(feature_name)
    )


def aggregate_previous_application(prev: pd.DataFrame) -> pd.DataFrame:
    # Simple per-applicant aggregations (count / mean / max / min)
    agg = prev.groupby(ID_COLUMN).agg(
        prev_app_count=(ID_COLUMN, "count"),
        prev_amt_application_mean=("AMT_APPLICATION", "mean"),
        prev_amt_application_max=("AMT_APPLICATION", "max"),
        prev_amt_credit_mean=("AMT_CREDIT", "mean"),
        prev_amt_credit_max=("AMT_CREDIT", "max"),
        prev_amt_down_payment_mean=("AMT_DOWN_PAYMENT", "mean"),
        prev_amt_goods_price_mean=("AMT_GOODS_PRICE", "mean"),
        prev_interest_rate_primary_mean=("RATE_INTEREST_PRIMARY", "mean"),
        prev_interest_rate_privileged_mean=("RATE_INTEREST_PRIVILEGED", "mean"),
        prev_days_decision_mean=("DAYS_DECISION", "mean"),
        prev_days_decision_min=("DAYS_DECISION", "min"),
        prev_days_decision_max=("DAYS_DECISION", "max"),
    )

    # Count features by contract status
    status_counts = [
        ("Approved", "prev_approved_count"),
        ("Refused", "prev_refused_count"),
        ("Canceled", "prev_canceled_count"),
        ("Unused offer", "prev_unused_offer_count"),
    ]
    for value, name in status_counts:
        counts = _count_by_value(prev, STATUS_COL, value, name)
        agg = agg.join(counts, how="left")
        agg[name] = agg[name].fillna(0).astype(int)

    # Count features by contract type
    type_counts = [
        ("Cash loans", "prev_cash_loans_count"),
        ("Consumer loans", "prev_consumer_loans_count"),
        ("Revolving loans", "prev_revolving_loans_count"),
    ]
    for value, name in type_counts:
        counts = _count_by_value(prev, CONTRACT_TYPE_COL, value, name)
        agg = agg.join(counts, how="left")
        agg[name] = agg[name].fillna(0).astype(int)

    # Ratio features — prev_app_count is always >= 1, so division is safe
    agg["prev_approval_ratio"] = agg["prev_approved_count"] / agg["prev_app_count"]
    agg["prev_refusal_ratio"] = agg["prev_refused_count"] / agg["prev_app_count"]
    agg["prev_canceled_ratio"] = agg["prev_canceled_count"] / agg["prev_app_count"]

    agg = agg.reset_index()
    logger.info(
        "Previous application aggregated: %d applicants, %d features",
        len(agg),
        len(agg.columns) - 1,
    )
    return agg


def save_aggregated(agg: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    agg.to_parquet(output_path, index=False)
    logger.info("Saved previous application features to %s", output_path)


def print_summary(agg: pd.DataFrame) -> None:
    feature_cols = [c for c in agg.columns if c != ID_COLUMN]
    print("\n=== CreditLens AI Phase 7 - Previous Application Feature Engineering ===\n")
    print(f"  Applicants with prior applications : {len(agg):,}")
    print(f"  Features created                   : {len(feature_cols)}")
    print()
    print("  Feature names:")
    for col in feature_cols:
        print(f"    - {col}")
    print()
    print("  Descriptive statistics:")
    print(agg[feature_cols].describe().round(2).to_string())
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CreditLens AI Phase 7: Previous application feature engineering"
    )
    parser.add_argument(
        "--prev-app-path",
        type=Path,
        default=Path(
            "C:/Users/sidpu/OneDrive/Desktop/home-credit-default-risk/previous_application.csv"
        ),
        help="Path to previous_application.csv",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/processed/previous_application_aggregated.parquet"),
        help="Output path for aggregated previous application parquet",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    prev = load_previous_application(args.prev_app_path)
    agg = aggregate_previous_application(prev)
    save_aggregated(agg, args.output_path)
    print_summary(agg)


if __name__ == "__main__":
    main()
