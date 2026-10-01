"""API tests: real FastAPI app + real repository on in-memory SQLite,
with a fake model (prediction = lag_1 + 1) and synthetic hourly history."""

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.deps import get_forecast_repository
from app.db.database import Base, get_db
from app.main import create_app
from app.models.database_models import Forecast, PredictionLog
from app.repositories.forecast_repository import ForecastRepository
from app.services.feature_service import FeatureService
from app.services.forecast_service import ForecastService
from app.services.history_provider import InMemoryHistory

COLUMNS = ["lag_1", "lag_24", "rolling_mean_3", "hour_sin"]
ORIGIN = "2026-01-10T00:00:00"


class FakeModelService:
    feature_columns = COLUMNS
    is_loaded = True
    model_version = "v-test"

    def predict(self, frame):
        return frame["lag_1"].to_numpy() + 1.0

    def get_model_info(self):
        return {
            "model_name": "FakeModel",
            "model_version": "v-test",
            "feature_count": len(COLUMNS),
            "feature_columns": COLUMNS,
            "config": {"model_name": "FakeModel", "model_version": "v-test"},
            "loaded_at": "2026-09-30T00:00:00+00:00",
        }

    def get_metrics(self):
        return {"mae": 1.5}

    def get_feature_importance(self):
        return [{"feature": "lag_1", "importance": "10"}]


@pytest.fixture
def env(monkeypatch):
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)

    def override_db():
        with Session(engine) as session:
            yield session

    idx = pd.date_range("2026-01-01", periods=300, freq="h")
    history = InMemoryHistory(pd.Series(np.arange(300, dtype=float), index=idx))
    model = FakeModelService()
    app = create_app()
    app.state.model_service = model
    app.state.forecast_service = ForecastService(model, FeatureService(COLUMNS), history, ForecastRepository())
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr("app.api.routes.health.check_database", lambda: True)
    return TestClient(app), engine, app


def count(engine, model):
    with Session(engine) as s:
        return s.execute(select(func.count()).select_from(model)).scalar_one()


def test_health_ok_and_degraded(env):
    client, _, app = env
    body = client.get("/health").json()
    assert body == {"status": "ok", "model_loaded": True, "history_loaded": True, "database_ok": True}
    app.state.forecast_service = None
    assert client.get("/health").json()["status"] == "degraded"


def test_predict_returns_forecast_and_persists(env):
    client, engine, _ = env
    r = client.post("/predict", json={"timestamp": ORIGIN, "horizon": 24})
    assert r.status_code == 200
    body = r.json()
    assert body["model"] == "FakeModel" and body["unit"] == "kWh" and body["horizon"] == 24
    assert len(body["forecast"]) == 24
    assert body["forecast"][0]["timestamp"] == "2026-01-10T01:00:00"
    assert body["forecast"][0]["predicted_energy_kwh"] == 217.0
    assert count(engine, Forecast) == 24
    assert count(engine, PredictionLog) == 1


def test_predict_defaults_to_24_hours(env):
    client, _, _ = env
    assert len(client.post("/predict", json={"timestamp": ORIGIN}).json()["forecast"]) == 24


def test_predict_supports_168_hours(env):
    client, _, _ = env
    r = client.post("/predict", json={"timestamp": "2026-01-09T00:00:00", "horizon": 168})
    assert r.status_code == 200 and len(r.json()["forecast"]) == 168


def test_predict_validation_errors(env):
    client, engine, _ = env
    for payload in (
        {"timestamp": ORIGIN, "horizon": 0},
        {"timestamp": ORIGIN, "horizon": 169},
        {"timestamp": ORIGIN, "horizon": "abc"},
        {"timestamp": "not-a-date", "horizon": 24},
        {"horizon": 24},
    ):
        assert client.post("/predict", json=payload).status_code == 422, payload
    assert count(engine, Forecast) == 0


def test_predict_domain_errors_are_422_and_logged(env):
    client, engine, _ = env
    r = client.post("/predict", json={"timestamp": "2026-01-10T00:30:00", "horizon": 24})
    assert r.status_code == 422 and r.json()["error"] == "InvalidTimestampError"
    r = client.post("/predict", json={"timestamp": "2026-01-10T00:00:00Z", "horizon": 24})
    assert r.status_code == 422
    r = client.post("/predict", json={"timestamp": "2027-01-01T00:00:00", "horizon": 24})
    assert r.status_code == 422 and r.json()["error"] == "InsufficientHistoryError"
    assert count(engine, Forecast) == 0
    assert count(engine, PredictionLog) == 3


def test_predict_503_when_service_unavailable(env):
    client, _, app = env
    app.state.forecast_service = None
    r = client.post("/predict", json={"timestamp": ORIGIN, "horizon": 24})
    assert r.status_code == 503 and r.json()["error"] == "ModelNotLoadedError"


def test_predict_503_on_database_failure(env):
    client, _, app = env

    class BrokenRepo(ForecastRepository):
        def save_forecasts(self, *a, **k):
            from app.core.exceptions import PersistenceError

            raise PersistenceError("db down")

    svc = app.state.forecast_service
    app.state.forecast_service = ForecastService(FakeModelService(), FeatureService(COLUMNS), svc._history, BrokenRepo())
    r = client.post("/predict", json={"timestamp": ORIGIN, "horizon": 24})
    assert r.status_code == 503 and r.json()["error"] == "PersistenceError"


def test_batch_predict_isolates_bad_items(env):
    client, engine, _ = env
    payload = {"requests": [{"timestamp": ORIGIN, "horizon": 24}, {"timestamp": "2026-01-10T00:30:00", "horizon": 24}]}
    r = client.post("/batch-predict", json=payload)
    assert r.status_code == 200
    results = r.json()["results"]
    assert results[0]["success"] is True and len(results[0]["result"]["forecast"]) == 24
    assert results[1]["success"] is False and "InvalidTimestampError" in results[1]["error"]
    assert count(engine, Forecast) == 24
    assert client.post("/batch-predict", json={"requests": []}).status_code == 422


def test_model_info_and_metrics(env):
    client, _, app = env
    info = client.get("/model-info").json()
    assert info["model_name"] == "FakeModel" and info["target"] == "energy_kwh"
    assert info["frequency"] == "Hourly" and info["feature_count"] == 4
    m = client.get("/metrics").json()
    assert m["metrics"] == {"mae": 1.5} and m["feature_importance"][0]["feature"] == "lag_1"
    app.state.model_service = None
    assert client.get("/model-info").status_code == 503
    assert client.get("/metrics").status_code == 503


def test_forecast_history_pagination_sorting_and_filters(env):
    client, _, _ = env
    client.post("/predict", json={"timestamp": ORIGIN, "horizon": 24})
    client.post("/predict", json={"timestamp": "2026-01-09T00:00:00", "horizon": 24})

    body = client.get("/forecast-history", params={"page": 1, "page_size": 10}).json()
    assert body["total"] == 48 and len(body["items"]) == 10 and body["page"] == 1
    item = body["items"][0]
    assert {"forecast_timestamp", "prediction_timestamp", "predicted_energy_kwh", "model_version", "horizon", "created_at"} <= set(item)

    last_page = client.get("/forecast-history", params={"page": 5, "page_size": 10}).json()
    assert len(last_page["items"]) == 8

    asc = client.get("/forecast-history", params={"sort_by": "predicted_energy_kwh", "order": "asc"}).json()["items"]
    values = [i["predicted_energy_kwh"] for i in asc]
    assert values == sorted(values)

    today = date.today()
    assert client.get("/forecast-history", params={"date_from": (today + timedelta(days=2)).isoformat()}).json()["total"] == 0
    assert client.get("/forecast-history", params={"date_from": (today - timedelta(days=1)).isoformat(), "date_to": (today + timedelta(days=1)).isoformat()}).json()["total"] == 48

    assert client.get("/forecast-history", params={"sort_by": "bogus"}).status_code == 422
    assert client.get("/forecast-history", params={"page": 0}).status_code == 422
    assert client.get("/forecast-history", params={"page_size": 1000}).status_code == 422
    r = client.get("/forecast-history", params={"date_from": "2026-02-01", "date_to": "2026-01-01"})
    assert r.status_code == 422


def test_history_repository_dependency_is_overridable(env):
    client, _, app = env
    app.dependency_overrides[get_forecast_repository] = lambda: ForecastRepository()
    assert client.get("/forecast-history").status_code == 200
