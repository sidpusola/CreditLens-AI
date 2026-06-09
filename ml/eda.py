from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_dataset(dataset_path: Path) -> pd.DataFrame:
    if not dataset_path.exists():
        logger.error("Dataset file does not exist: %s", dataset_path)
        raise FileNotFoundError(f"Dataset file does not exist: {dataset_path}")

    try:
        df = pd.read_csv(dataset_path)
        logger.info("Loaded dataset from %s", dataset_path)
        return df
    except pd.errors.ParserError as exc:
        logger.exception("Failed to parse CSV file: %s", dataset_path)
        raise
    except Exception as exc:
        logger.exception("Unexpected error while loading dataset: %s", dataset_path)
        raise


def summarize_shape(df: pd.DataFrame) -> Tuple[int, int]:
    shape = df.shape
    logger.info("Dataset shape: %s rows, %s columns", shape[0], shape[1])
    return shape


def compute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(ascending=False).to_frame(name="missing_count")
    missing["missing_ratio"] = missing["missing_count"] / len(df)
    logger.info("Computed missing value statistics for dataset")
    return missing


def get_target_distribution(df: pd.DataFrame, target_column: str = "TARGET") -> pd.Series:
    if target_column not in df.columns:
        logger.error("Target column %s not found in dataset", target_column)
        raise KeyError(f"Target column '{target_column}' not found in dataset")

    distribution = df[target_column].value_counts(dropna=False).sort_index()
    logger.info("Computed target distribution for column %s", target_column)
    return distribution


def identify_feature_types(
    df: pd.DataFrame,
    categorical_threshold: int = 20,
    excluded_columns: List[str] = None,
) -> Tuple[List[str], List[str]]:
    excluded_columns = excluded_columns or []
    categorical_columns: List[str] = []
    numerical_columns: List[str] = []

    for column in df.columns:
        if column in excluded_columns:
            continue

        dtype = df[column].dtype
        unique_count = df[column].nunique(dropna=False)

        if pd.api.types.is_numeric_dtype(dtype) and unique_count > categorical_threshold:
            numerical_columns.append(column)
        else:
            categorical_columns.append(column)

    logger.info(
        "Identified %s categorical and %s numerical columns",
        len(categorical_columns),
        len(numerical_columns),
    )
    return categorical_columns, numerical_columns


def generate_recommendations(
    missing_df: pd.DataFrame,
    categorical_columns: List[str],
    numerical_columns: List[str],
    target_distribution: pd.Series,
) -> List[str]:
    recommendations: List[str] = []

    recommendations.append(
        "Review columns with the highest missing ratios and determine whether to drop, impute, or exclude them from modeling."
    )

    if len(categorical_columns) > 0:
        recommendations.append(
            "Create a preprocessing plan for categorical columns, including encoding strategies for low-cardinality and high-cardinality features."
        )

    if len(numerical_columns) > 0:
        recommendations.append(
            "Standardize or scale numerical features where appropriate, especially for models sensitive to feature magnitude."
        )

    if target_distribution.min() / target_distribution.max() < 0.5:
        recommendations.append(
            "The target appears imbalanced; consider evaluation metrics such as ROC-AUC, precision, recall, and F1, and potentially resampling if needed."
        )
    else:
        recommendations.append(
            "Target distribution is reasonably balanced, but continue monitoring class balance during preprocessing and validation."
        )

    if not missing_df.empty and missing_df.iloc[0].missing_ratio > 0.5:
        recommendations.append(
            "Some features have more than 50% missing data; these features should be carefully evaluated for utility before inclusion."
        )

    if "SK_ID_CURR" in numerical_columns:
        recommendations.append(
            "Exclude identifier columns such as SK_ID_CURR from model training."
        )

    logger.info("Generated EDA recommendations")
    return recommendations


def print_report(
    shape: Tuple[int, int],
    missing_df: pd.DataFrame,
    target_distribution: pd.Series,
    categorical_columns: List[str],
    numerical_columns: List[str],
    recommendations: List[str],
) -> None:
    print("\n=== CreditLens AI Phase 2 EDA Report ===\n")
    print(f"Dataset shape: {shape[0]} rows, {shape[1]} columns\n")

    print("Missing values summary:\n")
    if missing_df.empty:
        print("No missing values detected.\n")
    else:
        print(missing_df.head(20).to_string())
        print("\n")

    print("Target distribution (TARGET):\n")
    print(target_distribution.to_string())
    print("\n")

    print("Categorical columns:\n")
    print(", ".join(categorical_columns[:50]) or "None")
    print("\n")

    print("Numerical columns:\n")
    print(", ".join(numerical_columns[:50]) or "None")
    print("\n")

    print("Recommendations:\n")
    for recommendation in recommendations:
        print(f"- {recommendation}")
    print("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CreditLens AI Phase 2 EDA")
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=Path("C:/Users/sidpu/OneDrive/Desktop/home-credit-default-risk/application_train.csv"),
        help="Path to application_train.csv file",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    dataset_path = args.dataset_path
    df = load_dataset(dataset_path)

    shape = summarize_shape(df)
    missing_df = compute_missing_values(df)
    target_distribution = get_target_distribution(df, target_column="TARGET")
    categorical_columns, numerical_columns = identify_feature_types(
        df,
        categorical_threshold=20,
        excluded_columns=["SK_ID_CURR", "TARGET"],
    )
    recommendations = generate_recommendations(
        missing_df=missing_df,
        categorical_columns=categorical_columns,
        numerical_columns=numerical_columns,
        target_distribution=target_distribution,
    )

    print_report(
        shape=shape,
        missing_df=missing_df,
        target_distribution=target_distribution,
        categorical_columns=categorical_columns,
        numerical_columns=numerical_columns,
        recommendations=recommendations,
    )


if __name__ == "__main__":
    main()
