from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ID_COLUMN = "SK_ID_CURR"
# Load only the columns the features need (file is ~400 MB)
USE_COLUMNS = [
    "SK_ID_CURR",
    "MONTHS_BALANCE",
    "AMT_BALANCE",
    "AMT_CREDIT_LIMIT_ACTUAL",
    "AMT_DRAWINGS_CURRENT",
    "AMT_DRAWINGS_ATM_CURRENT",
    "AMT_INST_MIN_REGULARITY",
    "AMT_PAYMENT_CURRENT",
    "SK_DPD",
    "SK_DPD_DEF",
    "NAME_CONTRACT_STATUS",
]
# Balance / limit above this fraction counts as "high utilization"
HIGH_UTILIZATION_THRESHOLD = 0.8


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_credit_card(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"credit_card_balance.csv not found at {path}")
    df = pd.read_csv(path, usecols=USE_COLUMNS)
    logger.info("Loaded credit_card_balance: %d rows, %d columns", *df.shape)
    return df


def print_eda(df: pd.DataFrame) -> None:
    print("\n=== CreditLens AI Phase 9 - credit_card_balance EDA ===\n")
    print(f"  Total rows          : {len(df):,}")
    print(f"  Unique applicants   : {df[ID_COLUMN].nunique():,}")
    print(f"  Avg rows/applicant  : {len(df) / df[ID_COLUMN].nunique():.1f}")
    print()
    print("  Missing values (key financial columns):")
    key_cols = [
        "AMT_BALANCE",
        "AMT_CREDIT_LIMIT_ACTUAL",
        "AMT_DRAWINGS_CURRENT",
        "AMT_INST_MIN_REGULARITY",
        "AMT_PAYMENT_CURRENT",
        "SK_DPD",
        "SK_DPD_DEF",
    ]
    missing = df[key_cols].isna().sum()
    for col in key_cols:
        ratio = 100.0 * missing[col] / len(df)
        print(f"    {col:<28} {missing[col]:>10,} ({ratio:5.1f}%)")
    print()


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Utilization = balance / credit limit; undefined when limit is 0
    df["cc_utilization"] = np.where(
        df["AMT_CREDIT_LIMIT_ACTUAL"] > 0,
        df["AMT_BALANCE"] / df["AMT_CREDIT_LIMIT_ACTUAL"],
        np.nan,
    )
    # Payment ratio = actual payment / minimum required payment
    df["cc_payment_ratio"] = np.where(
        df["AMT_INST_MIN_REGULARITY"] > 0,
        df["AMT_PAYMENT_CURRENT"] / df["AMT_INST_MIN_REGULARITY"],
        np.nan,
    )
    df["is_high_util"] = df["cc_utilization"] > HIGH_UTILIZATION_THRESHOLD
    df["is_active"] = df["NAME_CONTRACT_STATUS"] == "Active"
    return df


def aggregate_credit_card(df: pd.DataFrame) -> pd.DataFrame:
    df = add_derived_columns(df)

    agg = df.groupby(ID_COLUMN).agg(
        cc_record_count=(ID_COLUMN, "count"),
        cc_avg_balance=("AMT_BALANCE", "mean"),
        cc_max_balance=("AMT_BALANCE", "max"),
        cc_min_balance=("AMT_BALANCE", "min"),
        cc_avg_credit_limit=("AMT_CREDIT_LIMIT_ACTUAL", "mean"),
        cc_max_credit_limit=("AMT_CREDIT_LIMIT_ACTUAL", "max"),
        cc_min_credit_limit=("AMT_CREDIT_LIMIT_ACTUAL", "min"),
        cc_avg_utilization_ratio=("cc_utilization", "mean"),
        cc_max_utilization_ratio=("cc_utilization", "max"),
        cc_high_utilization_count=("is_high_util", "sum"),
        cc_avg_payment=("AMT_PAYMENT_CURRENT", "mean"),
        cc_total_payment=("AMT_PAYMENT_CURRENT", "sum"),
        cc_avg_payment_ratio=("cc_payment_ratio", "mean"),
        cc_min_payment_ratio=("cc_payment_ratio", "min"),
        cc_avg_drawings=("AMT_DRAWINGS_CURRENT", "mean"),
        cc_total_drawings=("AMT_DRAWINGS_CURRENT", "sum"),
        _total_atm_drawings=("AMT_DRAWINGS_ATM_CURRENT", "sum"),
        cc_avg_dpd=("SK_DPD", "mean"),
        cc_max_dpd=("SK_DPD", "max"),
        cc_avg_dpd_def=("SK_DPD_DEF", "mean"),
        cc_max_dpd_def=("SK_DPD_DEF", "max"),
        cc_active_months=("is_active", "sum"),
        cc_recent_activity_months=("MONTHS_BALANCE", "max"),
    )

    # Integer count features
    for col in ["cc_high_utilization_count", "cc_active_months"]:
        agg[col] = agg[col].astype(int)

    # cc_record_count is always >= 1, so division is safe
    agg["cc_high_utilization_ratio"] = (
        agg["cc_high_utilization_count"] / agg["cc_record_count"]
    )

    # Cash advance ratio = ATM drawings / total drawings; 0 when no drawings
    agg["cc_cash_advance_ratio"] = np.where(
        agg["cc_total_drawings"] > 0,
        agg["_total_atm_drawings"] / agg["cc_total_drawings"],
        0.0,
    )
    agg = agg.drop(columns=["_total_atm_drawings"])

    agg = agg.reset_index()
    logger.info(
        "Credit card aggregated: %d applicants, %d features",
        len(agg),
        len(agg.columns) - 1,
    )
    return agg


def save_aggregated(agg: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    agg.to_parquet(output_path, index=False)
    logger.info("Saved credit card features to %s", output_path)


def print_summary(agg: pd.DataFrame) -> None:
    feature_cols = [c for c in agg.columns if c != ID_COLUMN]
    print("=== CreditLens AI Phase 9 - Credit Card Behavior Features ===\n")
    print(f"  Applicants with credit card history : {len(agg):,}")
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
        description="CreditLens AI Phase 9: Credit card balance feature engineering"
    )
    parser.add_argument(
        "--credit-card-path",
        type=Path,
        default=Path(
            "C:/Users/sidpu/OneDrive/Desktop/home-credit-default-risk/credit_card_balance.csv"
        ),
        help="Path to credit_card_balance.csv",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/processed/credit_card_aggregated.parquet"),
        help="Output path for aggregated credit card parquet",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    df = load_credit_card(args.credit_card_path)
    print_eda(df)
    agg = aggregate_credit_card(df)
    save_aggregated(agg, args.output_path)
    print_summary(agg)


if __name__ == "__main__":
    main()
