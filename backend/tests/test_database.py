from datetime import datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import Base, get_db
from app.models.database_models import Forecast, ModelMetadata, PredictionLog

BACKEND_DIR = Path(__file__).resolve().parents[1]
EXPECTED_TABLES = {"dataset_metadata", "model_metadata", "forecasts", "prediction_logs"}


@pytest.fixture
def engine():
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


def test_all_expected_tables_are_defined():
    assert EXPECTED_TABLES <= set(Base.metadata.tables)


def test_forecast_round_trip(engine):
    with Session(engine) as db:
        db.add(
            Forecast(
                forecast_timestamp=datetime(2026, 9, 30, 10),
                prediction_timestamp=datetime(2026, 9, 30, 11),
                predicted_energy_kwh=4.25,
                model_version="v-test",
                horizon=24,
                request_id="r1",
            )
        )
        db.commit()
        row = db.query(Forecast).one()
        assert row.predicted_energy_kwh == 4.25
        assert row.created_at is not None


def test_json_columns_and_unique_model_version(engine):
    with Session(engine) as db:
        db.add(ModelMetadata(model_name="LightGBM", model_version="v1", metrics={"k": 1}, is_active=True))
        db.add(PredictionLog(request_id="r1", endpoint="/predict", request_payload={"h": 24}, status="success"))
        db.commit()
        assert db.query(ModelMetadata).one().metrics == {"k": 1}
        db.add(ModelMetadata(model_name="LightGBM", model_version="v1", is_active=False))
        with pytest.raises(Exception):
            db.commit()


def test_get_db_yields_and_closes_session(monkeypatch):
    import app.db.database as dbmod

    monkeypatch.setattr(dbmod, "get_session_factory", lambda: (lambda: Session(create_engine("sqlite://"))))
    gen = get_db()
    session = next(gen)
    assert isinstance(session, Session)
    with pytest.raises(StopIteration):
        next(gen)


def test_alembic_upgrade_matches_models(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    try:
        cfg = Config(str(BACKEND_DIR / "alembic.ini"))
        cfg.set_main_option("script_location", str(BACKEND_DIR / "app/db/migrations"))
        command.upgrade(cfg, "head")

        eng = create_engine(url)
        assert EXPECTED_TABLES <= set(inspect(eng).get_table_names())
        with eng.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        assert diff == [], f"Migration drifted from models: {diff}"
    finally:
        get_settings.cache_clear()
