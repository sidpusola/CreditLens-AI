"""
Seed Supabase with REAL historical precedents so similar-case retrieval surfaces
applicants with genuine repayment outcomes (Defaulted / Repaid).

Uses the held-out test split (X_test + y_test) — these are real applicants the model
never trained on, with known TARGET labels. Each is scored, embedded, and inserted with
its actual outcome.

Prerequisites (run once in Supabase SQL editor): schema.sql, pgvector.sql, case.sql, outcome.sql
And in .env: SUPABASE_URL, SUPABASE_KEY, ENABLE_VECTOR_SEARCH=true
"""
from __future__ import annotations

import argparse
import logging
import math
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.model_service import get_model_service  # noqa: E402
from backend.services.supabase_service import get_supabase_service  # noqa: E402

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _clean(row: dict) -> dict:
    # JSON can't hold NaN — drop missing values (the model imputes them anyway)
    return {k: v for k, v in row.items() if not (isinstance(v, float) and math.isnan(v))}


def _confidence(p: float) -> float:
    return round(abs(p - 0.5) * 2 * 100, 1)


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Seed historical precedents into Supabase")
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "processed")
    parser.add_argument("--count", type=int, default=150, help="Number of precedents to seed")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    supabase = get_supabase_service()
    if not supabase.enabled:
        raise SystemExit("Supabase not configured — set SUPABASE_URL / SUPABASE_KEY in .env")

    X = pd.read_parquet(args.data_dir / "X_test.parquet")
    y = pd.read_parquet(args.data_dir / "y_test.parquet").squeeze()
    sample = X.sample(n=min(args.count, len(X)), random_state=args.seed)

    model = get_model_service()
    logger.info("Seeding %d precedents ...", len(sample))

    seeded = 0
    for pos, (idx, row) in enumerate(sample.iterrows(), start=1):
        features = _clean(row.to_dict())
        target = int(y.loc[idx])
        prediction = model.predict(features)
        explanation = model.explain(features)
        embedding = model.embed(features)
        record = {
            "risk_score": prediction["risk_score"],
            "default_probability": prediction["default_probability"],
            "risk_category": prediction["risk_category"],
            "confidence": _confidence(prediction["default_probability"]),
            "top_risk_factors": explanation["top_risk_factors"],
            "top_protective_factors": explanation["top_protective_factors"],
            "inputs": features,
            "outcome": "Defaulted" if target == 1 else "Repaid",
            "case_meta": {
                "applicant_id": f"HIST-{int(idx)}",
                "applicant_name": f"Historical Case {int(idx)}",
                "loan_amount": features.get("AMT_CREDIT"),
                "loan_purpose": "Historical precedent",
                "officer_name": "System (seed)",
            },
        }
        try:
            supabase.save_assessment(record, embedding=embedding)
            seeded += 1
        except Exception as exc:
            logger.warning("Failed to seed row %s: %s", idx, exc)
        if pos % 25 == 0:
            logger.info("  %d / %d", pos, len(sample))

    logger.info("Done. Seeded %d precedents with real outcomes.", seeded)
    print(f"\nSeeded {seeded} historical precedents (Defaulted/Repaid) into Supabase.\n")


if __name__ == "__main__":
    main()
