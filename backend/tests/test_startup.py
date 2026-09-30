"""Lifespan wiring: the app loads artifacts once at startup and degrades gracefully."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.database import Base, get_db
from app.main import create_app
from tests.artifact_factory import write_artifacts


def configure(monkeypatch, model_path, artifacts_dir, history_path):
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv("ARTIFACTS_DIR", str(artifacts_dir))
    monkeypatch.setenv("HISTORY_DATA_PATH", str(history_path))
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_settings():
    yield
    get_settings.cache_clear()


@pytest.fixture
def sqlite_override():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)

    def override():
        with Session(engine) as session:
            yield session

    return override


def test_startup_with_valid_artifacts_serves_predictions(tmp_path, monkeypatch, sqlite_override):
    art = write_artifacts(tmp_path)
    configure(monkeypatch, art.model_path, art.artifacts_dir, art.history_path)
    monkeypatch.setattr("app.api.routes.health.check_database", lambda: True)
    app = create_app()
    app.dependency_overrides[get_db] = sqlite_override
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        assert client.get("/model-info").json()["model_name"] == "StandInModel"
        r = client.post("/predict", json={"timestamp": "2026-01-15T00:00:00", "horizon": 24})
        assert r.status_code == 200 and len(r.json()["forecast"]) == 24
        assert client.get("/forecast-history").json()["total"] == 24


def test_startup_with_missing_model_degrades_instead_of_crashing(tmp_path, monkeypatch, sqlite_override):
    configure(monkeypatch, tmp_path / "nope.joblib", tmp_path / "artifacts", tmp_path / "nope.csv")
    monkeypatch.setattr("app.api.routes.health.check_database", lambda: True)
    app = create_app()
    app.dependency_overrides[get_db] = sqlite_override
    with TestClient(app) as client:
        health = client.get("/health").json()
        assert health["status"] == "degraded" and health["model_loaded"] is False
        assert client.get("/model-info").status_code == 503
        assert client.get("/metrics").status_code == 503
        r = client.post("/predict", json={"timestamp": "2026-01-15T00:00:00", "horizon": 24})
        assert r.status_code == 503


def test_startup_with_missing_history_keeps_model_but_disables_forecasts(tmp_path, monkeypatch, sqlite_override):
    art = write_artifacts(tmp_path)
    configure(monkeypatch, art.model_path, art.artifacts_dir, tmp_path / "missing.csv")
    monkeypatch.setattr("app.api.routes.health.check_database", lambda: True)
    app = create_app()
    app.dependency_overrides[get_db] = sqlite_override
    with TestClient(app) as client:
        health = client.get("/health").json()
        assert health["model_loaded"] is True and health["history_loaded"] is False
        assert client.get("/model-info").status_code == 200
        assert client.post("/predict", json={"timestamp": "2026-01-15T00:00:00"}).status_code == 503


def test_check_database_reports_true_and_false(monkeypatch):
    from app.api.routes import health

    monkeypatch.setattr(health, "get_engine", lambda: create_engine("sqlite://"))
    assert health.check_database() is True

    def broken():
        raise RuntimeError("no db")

    monkeypatch.setattr(health, "get_engine", broken)
    assert health.check_database() is False
