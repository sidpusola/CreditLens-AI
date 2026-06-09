from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ID_COLUMN = "SK_ID_CURR"
CREDIT_ACTIVE_COL = "CREDIT_ACTIVE"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_bureau(bureau_path: Path) -> pd.DataFrame:
    if not bureau_path.exists():
        raise FileNotFoundError(f"bureau.csv not found at {bureau_path}")
    df = pd.read_csv(bureau_path)
    logger.info("Loaded bureau: %d rows, %d columns", *df.shape)
    return df


def aggregate_bureau(bureau: pd.DataFrame) -> pd.DataFrame:
    agg = bureau.groupby(ID_COLUMN).agg(
        bureau_total_loans=(ID_COLUMN, "count"),
        bureau_total_credit=("AMT_CREDIT_SUM", "sum"),
        bureau_total_debt=("AMT_CREDIT_SUM_DEBT", "sum"),
        bureau_max_overdue=("AMT_CREDIT_MAX_OVERDUE", "max"),
        bureau_avg_overdue=("AMT_CREDIT_MAX_OVERDUE", "mean"),
        bureau_avg_credit_age=("DAYS_CREDIT", "mean"),
        bureau_avg_enddate=("DAYS_CREDIT_ENDDATE", "mean"),
    )

    # Active and closed counts require filtering by CREDIT_ACTIVE value
    for status, col_name in [
        ("Active", "bureau_active_count"),
        ("Closed", "bureau_closed_count"),
    ]:
        counts = (
            bureau[bureau[CREDIT_ACTIVE_COL] == status]
            .groupby(ID_COLUMN)
            .size()
            .rename(col_name)
        )
        agg = agg.join(counts, how="left")
        agg[col_name] = agg[col_name].fillna(0).astype(int)

    # Ratio: 0 when total credit is zero to avoid division by zero
    agg["bureau_debt_to_credit"] = np.where(
        agg["bureau_total_credit"] > 0,
        agg["bureau_total_debt"] / agg["bureau_total_credit"],
        0.0,
    )

    agg = agg.reset_index()
    logger.info(
        "Bureau aggregated: %d applicants, %d features",
        len(agg),
        len(agg.columns) - 1,
    )
    return agg


def save_aggregated(agg: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    agg.to_parquet(output_path, index=False)
    logger.info("Saved bureau aggregated features to %s", output_path)


def print_summary(agg: pd.DataFrame) -> None:
    feature_cols = [c for c in agg.columns if c != ID_COLUMN]
    print("\n=== CreditLens AI Phase 6 — Bureau Feature Engineering ===\n")
    print(f"  Applicants with bureau history : {len(agg):,}")
    print(f"  Features created               : {len(feature_cols)}")
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
        description="CreditLens AI Phase 6: Bureau credit history feature engineering"
    )
    parser.add_argument(
        "--bureau-path",
        type=Path,
        default=Path(
            "C:/Users/sidpu/OneDrive/Desktop/home-credit-default-risk/bureau.csv"
        ),
        help="Path to bureau.csv",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/processed/bureau_aggregated.parquet"),
        help="Output path for aggregated bureau parquet",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    bureau = load_bureau(args.bureau_path)
    agg = aggregate_bureau(bureau)
    save_aggregated(agg, args.output_path)
    print_summary(agg)


if __name__ == "__main__":
    main()
