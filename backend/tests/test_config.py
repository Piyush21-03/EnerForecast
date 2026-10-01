from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import PROJECT_ROOT, Settings


def make(**kwargs) -> Settings:
    return Settings(_env_file=None, **kwargs)


def test_database_url_is_required(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        make()


def test_defaults_and_relative_paths_resolve_to_project_root():
    s = make(database_url="postgresql://x")
    assert s.model_path == PROJECT_ROOT / "backend/models/lightgbm_energy_forecaster.joblib"
    assert s.metrics_path == PROJECT_ROOT / "backend/artifacts/metrics.json"


def test_absolute_paths_are_kept():
    abs_path = Path("/models/m.joblib").resolve()
    s = make(database_url="postgresql://x", model_path=abs_path)
    assert s.model_path == abs_path


def test_cors_origins_are_split_and_trimmed():
    s = make(database_url="postgresql://x", cors_origins="http://a.com, http://b.com ,")
    assert s.cors_origin_list == ["http://a.com", "http://b.com"]


def test_log_level_normalised_and_validated():
    assert make(database_url="postgresql://x", log_level="debug").log_level == "DEBUG"
    with pytest.raises(ValidationError):
        make(database_url="postgresql://x", log_level="loud")
