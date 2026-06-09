from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ID_COLUMN = "SK_ID_CURR"
# Only these columns are needed — avoids loading the full ~690 MB file into memory
USE_COLUMNS = [
    "SK_ID_CURR",
    "DAYS_INSTALMENT",
    "DAYS_ENTRY_PAYMENT",
    "AMT_INSTALMENT",
    "AMT_PAYMENT",
]
# Absolute currency tolerance for classifying a payment as exact vs under/over
PAYMENT_TOLERANCE = 1.0


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_installments(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"installments_payments.csv not found at {path}")
    df = pd.read_csv(path, usecols=USE_COLUMNS)
    logger.info("Loaded installments_payments: %d rows, %d columns", *df.shape)
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    # days_late > 0 means the payment was entered after it was due
    df["days_late"] = df["DAYS_ENTRY_PAYMENT"] - df["DAYS_INSTALMENT"]

    # payment_ratio = paid / prescribed; undefined when prescribed amount is 0
    df["payment_ratio"] = np.where(
        df["AMT_INSTALMENT"] > 0,
        df["AMT_PAYMENT"] / df["AMT_INSTALMENT"],
        np.nan,
    )

    # Classify each payment relative to what was owed
    amt_diff = df["AMT_PAYMENT"] - df["AMT_INSTALMENT"]
    df["is_late"] = df["days_late"] > 0
    df["is_underpayment"] = amt_diff < -PAYMENT_TOLERANCE
    df["is_overpayment"] = amt_diff > PAYMENT_TOLERANCE
    df["is_exact_payment"] = amt_diff.abs() <= PAYMENT_TOLERANCE
    return df


def aggregate_installments(df: pd.DataFrame) -> pd.DataFrame:
    df = add_derived_columns(df)

    agg = df.groupby(ID_COLUMN).agg(
        installment_count=("AMT_INSTALMENT", "count"),
        avg_installment_amount=("AMT_INSTALMENT", "mean"),
        max_installment_amount=("AMT_INSTALMENT", "max"),
        total_installment_amount=("AMT_INSTALMENT", "sum"),
        avg_days_late=("days_late", "mean"),
        max_days_late=("days_late", "max"),
        avg_payment_ratio=("payment_ratio", "mean"),
        min_payment_ratio=("payment_ratio", "min"),
        max_payment_ratio=("payment_ratio", "max"),
        late_payment_count=("is_late", "sum"),
        underpayment_count=("is_underpayment", "sum"),
        overpayment_count=("is_overpayment", "sum"),
        exact_payment_count=("is_exact_payment", "sum"),
        last_payment_days=("DAYS_ENTRY_PAYMENT", "max"),
        avg_payment_recency=("DAYS_ENTRY_PAYMENT", "mean"),
    )

    # Boolean sums come back as ints already, but be explicit
    for col in [
        "late_payment_count",
        "underpayment_count",
        "overpayment_count",
        "exact_payment_count",
    ]:
        agg[col] = agg[col].astype(int)

    # installment_count is always >= 1 per group, so division is safe
    agg["late_payment_ratio"] = agg["late_payment_count"] / agg["installment_count"]

    agg = agg.reset_index()
    logger.info(
        "Installments aggregated: %d applicants, %d features",
        len(agg),
        len(agg.columns) - 1,
    )
    return agg


def save_aggregated(agg: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    agg.to_parquet(output_path, index=False)
    logger.info("Saved installments features to %s", output_path)


def print_summary(agg: pd.DataFrame) -> None:
    feature_cols = [c for c in agg.columns if c != ID_COLUMN]
    print("\n=== CreditLens AI Phase 8 - Installment Payment Behavior Features ===\n")
    print(f"  Applicants with installment history : {len(agg):,}")
    print(f"  Features created                    : {len(feature_cols)}")
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
        description="CreditLens AI Phase 8: Installment payment behavior feature engineering"
    )
    parser.add_argument(
        "--installments-path",
        type=Path,
        default=Path(
            "C:/Users/sidpu/OneDrive/Desktop/home-credit-default-risk/installments_payments.csv"
        ),
        help="Path to installments_payments.csv",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/processed/installments_aggregated.parquet"),
        help="Output path for aggregated installments parquet",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    df = load_installments(args.installments_path)
    agg = aggregate_installments(df)
    save_aggregated(agg, args.output_path)
    print_summary(agg)


if __name__ == "__main__":
    main()
