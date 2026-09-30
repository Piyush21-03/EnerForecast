"""Application configuration, loaded from environment variables / .env.

No secrets are hardcoded. DATABASE_URL has no default on purpose, so a
missing value fails fast with a clear validation error.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> project root is three levels above "core"
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # .env also holds POSTGRES_* / VITE_* values used elsewhere
        case_sensitive=False,
    )

    app_name: str = "Energy Consumption Forecasting API"
    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = Field(..., min_length=1)

    model_path: Path = Path("backend/models/lightgbm_energy_forecaster.joblib")
    artifacts_dir: Path = Path("backend/artifacts")
    history_data_path: Path = Path("data/energy_consumption_hourly.csv")

    # Comma-separated string (kept as str so env parsing stays simple).
    cors_origins: str = "http://localhost:5173"

    @field_validator("log_level")
    @classmethod
    def _valid_log_level(cls, v: str) -> str:
        level = v.upper()
        if level not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
            raise ValueError(f"Invalid LOG_LEVEL: {v!r}")
        return level

    @field_validator("model_path", "artifacts_dir", "history_data_path")
    @classmethod
    def _resolve_from_project_root(cls, v: Path) -> Path:
        return v if v.is_absolute() else PROJECT_ROOT / v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # Artifact file locations (created by the Colab training notebook).
    @property
    def model_config_path(self) -> Path:
        return self.artifacts_dir / "model_config.json"

    @property
    def feature_columns_path(self) -> Path:
        return self.artifacts_dir / "feature_columns.json"

    @property
    def metrics_path(self) -> Path:
        return self.artifacts_dir / "metrics.json"

    @property
    def feature_importance_path(self) -> Path:
        return self.artifacts_dir / "feature_importance.csv"


@lru_cache
def get_settings() -> Settings:
    return Settings()
