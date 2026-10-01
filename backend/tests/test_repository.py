from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import PersistenceError
from app.db.database import Base
from app.models.database_models import Forecast, PredictionLog
from app.repositories.forecast_repository import ForecastRepository

ORIGIN = datetime(2026, 9, 30, 10)


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def points(n=5):
    return [(ORIGIN + timedelta(hours=i + 1), float(i)) for i in range(n)]


def save(db, request_id="r1", n=5, horizon=24):
    return ForecastRepository().save_forecasts(
        db, request_id=request_id, origin=ORIGIN, horizon=horizon, model_version="v1", points=points(n)
    )


def total(db, model=Forecast):
    return db.execute(select(func.count()).select_from(model)).scalar_one()


def test_save_forecasts_inserts_all_points(db):
    assert save(db) == 5
    rows = db.execute(select(Forecast).order_by(Forecast.prediction_timestamp)).scalars().all()
    assert [r.predicted_energy_kwh for r in rows] == [0.0, 1.0, 2.0, 3.0, 4.0]
    assert rows[0].forecast_timestamp == ORIGIN and rows[0].model_version == "v1" and rows[0].horizon == 24
    assert rows[0].created_at is not None


def test_save_forecasts_rolls_back_on_failure(db, monkeypatch):
    def boom():
        raise OperationalError("COMMIT", {}, Exception("db down"))

    monkeypatch.setattr(db, "commit", boom)
    with pytest.raises(PersistenceError):
        save(db)
    monkeypatch.undo()
    assert total(db) == 0


def test_add_prediction_log_success_and_failure(db, monkeypatch):
    repo = ForecastRepository()
    kwargs = dict(request_id="r1", endpoint="/predict", payload={"h": 24}, status="success",
                  error_message=None, latency_ms=12.5, model_version="v1")
    repo.add_prediction_log(db, **kwargs)
    log = db.execute(select(PredictionLog)).scalar_one()
    assert log.request_payload == {"h": 24} and log.latency_ms == 12.5

    monkeypatch.setattr(db, "commit", lambda: (_ for _ in ()).throw(SQLAlchemyError("down")))
    with pytest.raises(PersistenceError):
        repo.add_prediction_log(db, **kwargs)


def test_list_forecasts_pagination_and_total(db):
    save(db, "r1", n=25)
    repo = ForecastRepository()
    rows, count = repo.list_forecasts(db, page=1, page_size=10)
    assert count == 25 and len(rows) == 10
    rows, _ = repo.list_forecasts(db, page=3, page_size=10)
    assert len(rows) == 5
    rows, count = repo.list_forecasts(db, page=9, page_size=10)
    assert rows == [] and count == 25


def test_list_forecasts_sorting_is_stable(db):
    save(db, "r1", n=5)
    repo = ForecastRepository()
    asc, _ = repo.list_forecasts(db, page=1, page_size=10, sort_by="predicted_energy_kwh", order="asc")
    desc, _ = repo.list_forecasts(db, page=1, page_size=10, sort_by="predicted_energy_kwh", order="desc")
    assert [r.predicted_energy_kwh for r in asc] == [0.0, 1.0, 2.0, 3.0, 4.0]
    assert [r.predicted_energy_kwh for r in desc] == [4.0, 3.0, 2.0, 1.0, 0.0]
    ties, _ = repo.list_forecasts(db, page=1, page_size=10, sort_by="horizon", order="asc")
    assert [r.id for r in ties] == sorted((r.id for r in ties), reverse=True)  # tie-break: id desc


def test_list_forecasts_date_filter_is_inclusive(db):
    save(db, n=3)
    repo = ForecastRepository()
    today = date.today()
    _, inside = repo.list_forecasts(db, page=1, page_size=10, date_from=today, date_to=today)
    _, before = repo.list_forecasts(db, page=1, page_size=10, date_to=today - timedelta(days=1))
    _, after = repo.list_forecasts(db, page=1, page_size=10, date_from=today + timedelta(days=1))
    assert (inside, before, after) == (3, 0, 0)


def test_list_forecasts_rejects_unknown_sort_column(db):
    with pytest.raises(ValueError):
        ForecastRepository().list_forecasts(db, page=1, page_size=10, sort_by="id; DROP TABLE forecasts")


def test_list_forecasts_database_failure(db, monkeypatch):
    monkeypatch.setattr(db, "execute", lambda *a, **k: (_ for _ in ()).throw(SQLAlchemyError("down")))
    with pytest.raises(PersistenceError):
        ForecastRepository().list_forecasts(db, page=1, page_size=10)
