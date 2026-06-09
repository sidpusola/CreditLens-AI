from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

ID_COLUMN = "SK_ID_CURR"
BUREAU_ID_COLUMN = "SK_ID_BUREAU"
# STATUS codes: 'C'=closed, 'X'=unknown, '0'=current, '1'-'5'=increasing DPD severity
LATE_STATUSES = {"1", "2", "3", "4", "5"}
ACTIVE_STATUSES = {"0", "1", "2", "3", "4", "5"}  # account open and reporting
CLOSED_STATUS = "C"
# A month is "recent" if within this many months of the latest record (MONTHS_BALANCE == 0)
RECENT_WINDOW = 12


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_bureau_balance(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"bureau_balance.csv not found at {path}")
    df = pd.read_csv(path, dtype={"STATUS": "string"})
    logger.info("Loaded bureau_balance: %d rows, %d columns", *df.shape)
    return df


def load_bureau(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"bureau.csv not found at {path}")
    df = pd.read_csv(path, usecols=[ID_COLUMN, BUREAU_ID_COLUMN])
    logger.info("Loaded bureau (id map): %d rows", len(df))
    return df


def compute_max_consecutive_late(df: pd.DataFrame) -> pd.Series:
    """
    Longest run of consecutive late months within each SK_ID_BUREAU.
    Expects df already sorted by [SK_ID_BUREAU, MONTHS_BALANCE] with an `is_late` column.
    """
    is_late = df["is_late"]
    bureau = df[BUREAU_ID_COLUMN]
    # A new segment starts whenever is_late flips or we cross into a new bureau
    segment = ((is_late != is_late.shift()) | (bureau != bureau.shift())).cumsum()

    late_mask = is_late.to_numpy()
    late_rows = df.loc[late_mask, [BUREAU_ID_COLUMN]].copy()
    late_rows["segment"] = segment[late_mask].to_numpy()

    seg_sizes = late_rows.groupby([BUREAU_ID_COLUMN, "segment"]).size()
    max_consec = seg_sizes.groupby(level=BUREAU_ID_COLUMN).max()
    return max_consec.rename("bb_max_consecutive_late_months")


def aggregate_by_bureau(bb: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly bureau_balance rows to one row per SK_ID_BUREAU (8 features)."""
    bb = bb.sort_values([BUREAU_ID_COLUMN, "MONTHS_BALANCE"]).reset_index(drop=True)
    bb["is_late"] = bb["STATUS"].isin(LATE_STATUSES)
    bb["is_active"] = bb["STATUS"].isin(ACTIVE_STATUSES)
    bb["is_closed"] = bb["STATUS"] == CLOSED_STATUS
    bb["is_recent_late"] = bb["is_late"] & (bb["MONTHS_BALANCE"] >= -RECENT_WINDOW)

    agg = bb.groupby(BUREAU_ID_COLUMN).agg(
        bb_month_count=("STATUS", "count"),
        bb_recent_months=("MONTHS_BALANCE", "max"),
        bb_late_month_count=("is_late", "sum"),
        bb_recent_late_months=("is_recent_late", "sum"),
        bb_closed_status_ratio=("is_closed", "mean"),
        bb_active_status_ratio=("is_active", "mean"),
    )
    agg["bb_late_month_ratio"] = agg["bb_late_month_count"] / agg["bb_month_count"]

    # Max consecutive late streak (bureaus with no late months get 0)
    max_consec = compute_max_consecutive_late(bb)
    agg = agg.join(max_consec, how="left")
    agg["bb_max_consecutive_late_months"] = (
        agg["bb_max_consecutive_late_months"].fillna(0).astype(int)
    )

    agg = agg.reset_index()
    logger.info("Aggregated bureau_balance to %d bureau records", len(agg))
    return agg


def aggregate_to_applicant(bureau_with_bb: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse per-bureau features to one row per applicant.
    Each reducer is chosen to be meaningful at the applicant level.
    """
    agg = bureau_with_bb.groupby(ID_COLUMN).agg(
        bb_month_count=("bb_month_count", "mean"),
        bb_recent_months=("bb_recent_months", "max"),
        bb_late_month_count=("bb_late_month_count", "sum"),
        bb_late_month_ratio=("bb_late_month_ratio", "mean"),
        bb_max_consecutive_late_months=("bb_max_consecutive_late_months", "max"),
        bb_recent_late_months=("bb_recent_late_months", "sum"),
        bb_closed_status_ratio=("bb_closed_status_ratio", "mean"),
        bb_active_status_ratio=("bb_active_status_ratio", "mean"),
    )
    agg = agg.reset_index()
    logger.info(
        "Aggregated to applicant level: %d applicants, %d features",
        len(agg),
        len(agg.columns) - 1,
    )
    return agg


def build_features(bb: pd.DataFrame, bureau: pd.DataFrame) -> pd.DataFrame:
    bureau_agg = aggregate_by_bureau(bb)
    # Merge per-bureau features onto the bureau<->applicant id map
    merged = bureau.merge(bureau_agg, on=BUREAU_ID_COLUMN, how="inner")
    logger.info(
        "Merged bureau_balance into bureau: %d bureau records linked to applicants",
        len(merged),
    )
    return aggregate_to_applicant(merged)


def save_aggregated(agg: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    agg.to_parquet(output_path, index=False)
    logger.info("Saved bureau_balance features to %s", output_path)


def print_summary(agg: pd.DataFrame) -> None:
    feature_cols = [c for c in agg.columns if c != ID_COLUMN]
    print("\n=== CreditLens AI Phase 11 - Bureau Balance Monthly History Features ===\n")
    print(f"  Applicants with bureau-balance history : {len(agg):,}")
    print(f"  Features created                       : {len(feature_cols)}")
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
        description="CreditLens AI Phase 11: Bureau balance monthly history feature engineering"
    )
    parser.add_argument(
        "--bureau-balance-path",
        type=Path,
        default=Path(
            "C:/Users/sidpu/OneDrive/Desktop/home-credit-default-risk/bureau_balance.csv"
        ),
        help="Path to bureau_balance.csv",
    )
    parser.add_argument(
        "--bureau-path",
        type=Path,
        default=Path(
            "C:/Users/sidpu/OneDrive/Desktop/home-credit-default-risk/bureau.csv"
        ),
        help="Path to bureau.csv (provides SK_ID_BUREAU -> SK_ID_CURR mapping)",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/processed/bureau_balance_aggregated.parquet"),
        help="Output path for aggregated bureau_balance parquet",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    bb = load_bureau_balance(args.bureau_balance_path)
    bureau = load_bureau(args.bureau_path)
    agg = build_features(bb, bureau)
    save_aggregated(agg, args.output_path)
    print_summary(agg)


if __name__ == "__main__":
    main()
