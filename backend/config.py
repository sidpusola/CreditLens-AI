from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root (two levels up from this file: backend/config.py -> repo/)
REPO_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Application settings, overridable via environment variables (prefix CREDITLENS_)."""

    model_config = SettingsConfigDict(
        env_prefix="CREDITLENS_",
        env_file=".env",
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
