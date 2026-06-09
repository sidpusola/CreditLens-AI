from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

ID_COLUMN = "SK_ID_CURR"
PREV_ID_COLUMN = "SK_ID_PREV"
STATUS_COL = "NAME_CONTRACT_STATUS"
# POS_CASH_balance is small enough to load fully, but we only need these columns
USE_COLUMNS = [
    "SK_ID_PREV",
    "SK_ID_CURR",
    "MONTHS_BALANCE",
    "CNT_INSTALMENT",
    "CNT_INSTALMENT_FUTURE",
    "NAME_CONTRACT_STATUS",
    "SK_DPD",
    "SK_DPD_DEF",
]


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_pos_cash(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"POS_CASH_balance.csv not found at {path}")
    df = pd.read_csv(path, usecols=USE_COLUMNS)
    logger.info("Loaded POS_CASH_balance: %d rows, %d columns", *df.shape)
    return df


def _distinct_loans_by_status(
    df: pd.DataFrame, status: str, feature_name: str
) -> pd.Series:
    """Count distinct previous loans (SK_ID_PREV) per applicant with a given status."""
    return (
        df[df[STATUS_COL] == status]
        .groupby(ID_COLUMN)[PREV_ID_COLUMN]
        .nunique()
        .rename(feature_name)
    )


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Installments already paid on a loan = total term - installments remaining
    df["pos_completed_installments"] = df["CNT_INSTALMENT"] - df["CNT_INSTALMENT_FUTURE"]
    # A month is "late" if any days past due; "delinquent" if past the tolerated threshold
    df["is_late_month"] = df["SK_DPD"] > 0
    df["is_delinquent_month"] = df["SK_DPD_DEF"] > 0
    return df


def aggregate_pos_cash(df: pd.DataFrame) -> pd.DataFrame:
    df = add_derived_columns(df)

    agg = df.groupby(ID_COLUMN).agg(
        pos_record_count=(ID_COLUMN, "count"),
        pos_remaining_installments_mean=("CNT_INSTALMENT_FUTURE", "mean"),
        pos_remaining_installments_max=("CNT_INSTALMENT_FUTURE", "max"),
        pos_completed_installments_mean=("pos_completed_installments", "mean"),
        pos_avg_dpd=("SK_DPD", "mean"),
        pos_max_dpd=("SK_DPD", "max"),
        pos_avg_dpd_def=("SK_DPD_DEF", "mean"),
        pos_max_dpd_def=("SK_DPD_DEF", "max"),
        pos_late_payment_count=("is_late_month", "sum"),
        pos_delinquent_month_count=("is_delinquent_month", "sum"),
        pos_recent_months_active=("MONTHS_BALANCE", "max"),
        pos_avg_month_balance=("MONTHS_BALANCE", "mean"),
    )

    # Distinct active / completed previous loans
    active = _distinct_loans_by_status(df, "Active", "pos_active_loans")
    completed = _distinct_loans_by_status(df, "Completed", "pos_completed_loans")
    agg = agg.join(active, how="left").join(completed, how="left")
    agg["pos_active_loans"] = agg["pos_active_loans"].fillna(0).astype(int)
    agg["pos_completed_loans"] = agg["pos_completed_loans"].fillna(0).astype(int)

    # Ratio features — pos_record_count is always >= 1, so division is safe
    agg["pos_late_payment_ratio"] = (
        agg["pos_late_payment_count"] / agg["pos_record_count"]
    )
    agg["pos_delinquent_month_ratio"] = (
        agg["pos_delinquent_month_count"] / agg["pos_record_count"]
    )

    # Drop the intermediate count columns now that ratios are computed
    agg = agg.drop(columns=["pos_late_payment_count", "pos_delinquent_month_count"])

    agg = agg.reset_index()
    logger.info(
        "POS_CASH aggregated: %d applicants, %d features",
        len(agg),
        len(agg.columns) - 1,
    )
    return agg


def save_aggregated(agg: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    agg.to_parquet(output_path, index=False)
    logger.info("Saved POS_CASH features to %s", output_path)


def print_summary(agg: pd.DataFrame) -> None:
    feature_cols = [c for c in agg.columns if c != ID_COLUMN]
    print("\n=== CreditLens AI Phase 10 - POS_CASH Behavior Features ===\n")
    print(f"  Applicants with POS/cash history : {len(agg):,}")
    print(f"  Features created                 : {len(feature_cols)}")
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
        description="CreditLens AI Phase 10: POS_CASH_balance feature engineering"
    )
    parser.add_argument(
        "--pos-cash-path",
        type=Path,
        default=Path(
            "C:/Users/sidpu/OneDrive/Desktop/home-credit-default-risk/POS_CASH_balance.csv"
        ),
        help="Path to POS_CASH_balance.csv",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/processed/pos_cash_aggregated.parquet"),
        help="Output path for aggregated POS_CASH parquet",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    df = load_pos_cash(args.pos_cash_path)
    agg = aggregate_pos_cash(df)
    save_aggregated(agg, args.output_path)
    print_summary(agg)


if __name__ == "__main__":
    main()
