from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logger = logging.getLogger(__name__)

TARGET_COLUMN = "TARGET"
ID_COLUMN = "SK_ID_CURR"
TEST_SIZE = 0.2
RANDOM_STATE = 42
# Threshold must match eda.py — numeric columns with <= this many unique values
# are treated as categorical
CATEGORICAL_NUNIQUE_THRESHOLD = 20


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_aggregated_features(path: Path, source_name: str) -> Optional[pd.DataFrame]:
    if not path.exists():
        logger.warning(
            "%s aggregated file not found at %s — skipping merge", source_name, path
        )
        return None
    df = pd.read_parquet(path)
    logger.info(
        "Loaded %s aggregated features: %d rows, %d columns", source_name, *df.shape
    )
    return df


def merge_aggregated_features(
    df: pd.DataFrame,
    agg: pd.DataFrame,
    source_name: str,
) -> pd.DataFrame:
    """
    Left-join pre-aggregated (one-row-per-applicant) features onto the base dataset.
    Applicants absent from `agg` get NaN, which the median imputer handles downstream.
    The first non-ID column of `agg` is used as the match marker for logging.
    """
    before_cols = len(df.columns)
    marker_col = next(c for c in agg.columns if c != ID_COLUMN)
    merged = df.merge(agg, on=ID_COLUMN, how="left")
    n_matched = merged[marker_col].notna().sum()
    logger.info(
        "%s merge: %d / %d applicants matched (%.1f%%) — added %d features",
        source_name,
        n_matched,
        len(df),
        100.0 * n_matched / len(df),
        len(merged.columns) - before_cols,
    )
    return merged


def load_dataset(dataset_path: Path) -> pd.DataFrame:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    try:
        df = pd.read_csv(dataset_path)
        logger.info("Loaded dataset: %d rows, %d columns", *df.shape)
        return df
    except pd.errors.ParserError:
        logger.exception("Failed to parse CSV: %s", dataset_path)
        raise
    except Exception:
        logger.exception("Unexpected error loading dataset: %s", dataset_path)
        raise


def identify_columns(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    excluded = {TARGET_COLUMN, ID_COLUMN}
    numerical: List[str] = []
    categorical: List[str] = []

    for col in df.columns:
        if col in excluded:
            continue
        if (
            pd.api.types.is_numeric_dtype(df[col])
            and df[col].nunique() > CATEGORICAL_NUNIQUE_THRESHOLD
        ):
            numerical.append(col)
        else:
            categorical.append(col)

    logger.info(
        "Identified %d numerical and %d categorical feature columns",
        len(numerical),
        len(categorical),
    )
    return numerical, categorical


def build_preprocessor(
    numerical_columns: List[str],
    categorical_columns: List[str],
) -> ColumnTransformer:
    numerical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    # handle_unknown="ignore" silently passes zeros for unseen categories at inference time
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numerical_pipeline, numerical_columns),
            ("cat", categorical_pipeline, categorical_columns),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

    logger.info(
        "Preprocessor built: %d numerical transformers, %d categorical transformers",
        len(numerical_columns),
        len(categorical_columns),
    )
    return preprocessor


def split_features_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    X = df.drop(columns=[TARGET_COLUMN, ID_COLUMN], errors="ignore")
    y = df[TARGET_COLUMN]
    return X, y


def create_train_test_split(
    X: pd.DataFrame,
    y: pd.Series,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    logger.info(
        "Split complete — train: %d samples, test: %d samples",
        len(X_train),
        len(X_test),
    )
    return X_train, X_test, y_train, y_test


def fit_preprocessor(
    preprocessor: ColumnTransformer,
    X_train: pd.DataFrame,
) -> ColumnTransformer:
    # Fit only on training data — never on test data
    preprocessor.fit(X_train)
    logger.info("Preprocessor fitted on training data")
    return preprocessor


def save_preprocessor(preprocessor: ColumnTransformer, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, output_path)
    logger.info("Preprocessor saved to %s", output_path)


def save_column_metadata(
    numerical_columns: List[str],
    categorical_columns: List[str],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "numerical_columns": numerical_columns,
        "categorical_columns": categorical_columns,
        "target_column": TARGET_COLUMN,
        "id_column": ID_COLUMN,
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
    }
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Column metadata saved to %s", output_path)


def save_splits(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    X_train.to_parquet(output_dir / "X_train.parquet", index=False)
    X_test.to_parquet(output_dir / "X_test.parquet", index=False)
    y_train.to_frame().to_parquet(output_dir / "y_train.parquet", index=False)
    y_test.to_frame().to_parquet(output_dir / "y_test.parquet", index=False)
    logger.info("Raw train/test splits saved to %s", output_dir)


def print_summary(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    numerical_columns: List[str],
    categorical_columns: List[str],
    preprocessor: ColumnTransformer,
) -> None:
    # Transform a single row to get the output feature count cheaply
    n_output_features = preprocessor.transform(X_train.head(1)).shape[1]

    print("\n=== CreditLens AI Phase 3 — Preprocessing Summary ===\n")
    print(f"  Train samples         : {len(X_train):,}")
    print(f"  Test samples          : {len(X_test):,}")
    print(f"  Train target balance  : {y_train.value_counts(normalize=True).to_dict()}")
    print(f"  Test target balance   : {y_test.value_counts(normalize=True).to_dict()}")
    print(f"  Numerical features    : {len(numerical_columns)}")
    print(f"  Categorical features  : {len(categorical_columns)}")
    print(f"  Output features       : {n_output_features} (after OHE expansion)")
    print()
    print("  Numerical pipeline   : SimpleImputer(median) -> StandardScaler")
    print("  Categorical pipeline : SimpleImputer(most_frequent) -> OneHotEncoder")
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CreditLens AI Phase 3: Build and save preprocessing pipeline"
    )
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=Path(
            "C:/Users/sidpu/OneDrive/Desktop/home-credit-default-risk/application_train.csv"
        ),
        help="Path to application_train.csv",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=Path("models"),
        help="Directory to save preprocessor.joblib and column_metadata.json",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory to save raw train/test parquet splits",
    )
    parser.add_argument(
        "--bureau-path",
        type=Path,
        default=None,
        help="Path to bureau_aggregated.parquet (optional). If provided, merges bureau features.",
    )
    parser.add_argument(
        "--prev-app-path",
        type=Path,
        default=None,
        help=(
            "Path to previous_application_aggregated.parquet (optional). "
            "If provided, merges previous application features."
        ),
    )
    parser.add_argument(
        "--installments-path",
        type=Path,
        default=None,
        help=(
            "Path to installments_aggregated.parquet (optional). "
            "If provided, merges installment payment behavior features."
        ),
    )
    parser.add_argument(
        "--credit-card-path",
        type=Path,
        default=None,
        help=(
            "Path to credit_card_aggregated.parquet (optional). "
            "If provided, merges credit card behavior features."
        ),
    )
    parser.add_argument(
        "--pos-cash-path",
        type=Path,
        default=None,
        help=(
            "Path to pos_cash_aggregated.parquet (optional). "
            "If provided, merges POS/cash loan behavior features."
        ),
    )
    parser.add_argument(
        "--bureau-balance-path",
        type=Path,
        default=None,
        help=(
            "Path to bureau_balance_aggregated.parquet (optional). "
            "If provided, merges bureau monthly-history features."
        ),
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    df = load_dataset(args.dataset_path)

    if args.bureau_path is not None:
        bureau_agg = load_aggregated_features(args.bureau_path, "Bureau")
        if bureau_agg is not None:
            df = merge_aggregated_features(df, bureau_agg, "Bureau")

    if args.prev_app_path is not None:
        prev_agg = load_aggregated_features(args.prev_app_path, "Previous application")
        if prev_agg is not None:
            df = merge_aggregated_features(df, prev_agg, "Previous application")

    if args.installments_path is not None:
        inst_agg = load_aggregated_features(args.installments_path, "Installments")
        if inst_agg is not None:
            df = merge_aggregated_features(df, inst_agg, "Installments")

    if args.credit_card_path is not None:
        cc_agg = load_aggregated_features(args.credit_card_path, "Credit card")
        if cc_agg is not None:
            df = merge_aggregated_features(df, cc_agg, "Credit card")

    if args.pos_cash_path is not None:
        pos_agg = load_aggregated_features(args.pos_cash_path, "POS/cash")
        if pos_agg is not None:
            df = merge_aggregated_features(df, pos_agg, "POS/cash")

    if args.bureau_balance_path is not None:
        bb_agg = load_aggregated_features(args.bureau_balance_path, "Bureau balance")
        if bb_agg is not None:
            df = merge_aggregated_features(df, bb_agg, "Bureau balance")

    numerical_columns, categorical_columns = identify_columns(df)

    X, y = split_features_target(df)
    X_train, X_test, y_train, y_test = create_train_test_split(X, y)

    preprocessor = build_preprocessor(numerical_columns, categorical_columns)
    fit_preprocessor(preprocessor, X_train)

    save_preprocessor(preprocessor, args.models_dir / "preprocessor.joblib")
    save_column_metadata(
        numerical_columns,
        categorical_columns,
        args.models_dir / "column_metadata.json",
    )
    save_splits(X_train, X_test, y_train, y_test, args.data_dir)

    print_summary(
        X_train,
        X_test,
        y_train,
        y_test,
        numerical_columns,
        categorical_columns,
        preprocessor,
    )


if __name__ == "__main__":
    main()
