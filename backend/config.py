from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root (two levels up from this file: backend/config.py -> repo/)
REPO_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Application settings, overridable via environment variables (prefix CREDITLENS_)."""

    model_config = SettingsConfigDict(
        env_prefix="CREDITLENS_",
        # Load a .env from either the repo root or backend/ (later wins), so it
        # works no matter where uvicorn is launched from. Real env vars still win.
        env_file=(str(REPO_ROOT / ".env"), str(REPO_ROOT / "backend" / ".env")),
        extra="ignore",
        protected_namespaces=(),  # allow field names starting with "model_"
    )

    app_name: str = "CreditLens AI API"
    app_version: str = "1.0.0"
    log_level: str = "INFO"

    # Comma-separated allowed CORS origins (the Vite dev server runs on 5173)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # Directory holding the frozen production artifacts
    model_dir: Path = REPO_ROOT / "backend" / "models"

    # Risk-category thresholds on the 0-100 risk score
    medium_risk_threshold: float = 40.0
    high_risk_threshold: float = 70.0

    # Supabase (optional). Accepts the conventional SUPABASE_* names or the
    # prefixed CREDITLENS_SUPABASE_* names. Leave blank to disable persistence.
    supabase_url: str = Field(
        default="", validation_alias=AliasChoices("SUPABASE_URL", "CREDITLENS_SUPABASE_URL")
    )
    supabase_key: str = Field(
        default="", validation_alias=AliasChoices("SUPABASE_KEY", "CREDITLENS_SUPABASE_KEY")
    )
    supabase_table: str = Field(
        default="assessments",
        validation_alias=AliasChoices("SUPABASE_TABLE", "CREDITLENS_SUPABASE_TABLE"),
    )

    # Turn on only AFTER running backend/db/pgvector.sql. When off, embeddings are
    # not stored and the /assessments/similar endpoint reports unavailable.
    enable_vector_search: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_VECTOR_SEARCH", "CREDITLENS_ENABLE_VECTOR_SEARCH"),
    )

    # Local LLM (Ollama) for RAG-generated underwriting reports
    llm_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias=AliasChoices("LLM_BASE_URL", "CREDITLENS_LLM_BASE_URL"),
    )
    llm_model: str = Field(
        default="qwen3:4b",
        validation_alias=AliasChoices("LLM_MODEL", "CREDITLENS_LLM_MODEL"),
    )

    @property
    def supabase_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    @property
    def vector_search_enabled(self) -> bool:
        return self.supabase_enabled and self.enable_vector_search

    @property
    def model_path(self) -> Path:
        return self.model_dir / "xgboost_production.joblib"

    @property
    def preprocessor_path(self) -> Path:
        return self.model_dir / "preprocessor_production.joblib"

    @property
    def metadata_path(self) -> Path:
        return self.model_dir / "model_metadata.json"

    @property
    def column_metadata_path(self) -> Path:
        return self.model_dir / "column_metadata.json"


settings = Settings()
