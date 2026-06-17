from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, List, Optional

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


class SupabaseNotConfigured(RuntimeError):
    """Raised when a persistence call is made but Supabase env vars are unset."""


class SupabaseService:
    """
    Thin client over Supabase's REST (PostgREST) API using httpx.
    Avoids a heavy SDK dependency — the REST endpoints are all we need.
    """

    def __init__(self) -> None:
        self.enabled = settings.supabase_enabled
        self.table = settings.supabase_table
        if self.enabled:
            self._base = f"{settings.supabase_url.rstrip('/')}/rest/v1"
            self._headers = {
                "apikey": settings.supabase_key,
                "Authorization": f"Bearer {settings.supabase_key}",
                "Content-Type": "application/json",
            }
            logger.info("SupabaseService enabled (table=%s)", self.table)
        else:
            logger.info("SupabaseService disabled — SUPABASE_URL / SUPABASE_KEY not set")

    def _require(self) -> None:
        if not self.enabled:
            raise SupabaseNotConfigured(
                "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY to enable persistence."
            )

    @staticmethod
    def _to_pgvector(embedding: List[float]) -> str:
        # pgvector accepts a bracketed string literal: "[0.1,0.2,...]"
        return "[" + ",".join(repr(float(x)) for x in embedding) + "]"

    def save_assessment(self, record: Dict, embedding: Optional[List[float]] = None) -> Dict:
        self._require()
        payload = dict(record)
        if embedding is not None:
            payload["embedding"] = self._to_pgvector(embedding)
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{self._base}/{self.table}",
                headers={**self._headers, "Prefer": "return=representation"},
                json=payload,
            )
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if isinstance(rows, list) and rows else rows

    def match_assessments(self, embedding: List[float], match_count: int = 5) -> List[Dict]:
        """Find the most similar historical assessments via the match_assessments RPC."""
        self._require()
        with httpx.Client(timeout=15) as client:
            resp = client.post(
                f"{self._base}/rpc/match_assessments",
                headers=self._headers,
                json={"query_embedding": self._to_pgvector(embedding), "match_count": match_count},
            )
        resp.raise_for_status()
        return resp.json()

    def list_assessments(self, limit: int = 25) -> List[Dict]:
        self._require()
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{self._base}/{self.table}",
                headers=self._headers,
                params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
            )
        resp.raise_for_status()
        return resp.json()

    def get_assessment(self, assessment_id: str) -> Optional[Dict]:
        self._require()
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                f"{self._base}/{self.table}",
                headers=self._headers,
                params={"select": "*", "id": f"eq.{assessment_id}", "limit": "1"},
            )
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else None


@lru_cache(maxsize=1)
def get_supabase_service() -> SupabaseService:
    return SupabaseService()
