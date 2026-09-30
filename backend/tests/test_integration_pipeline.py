"""Real ModelService + FeatureService + CsvHistoryProvider + ForecastService."""

import numpy as np
import pandas as pd
import pytest

from app.core.exceptions import InsufficientHistoryError
from app.services.feature_service import (
    DEFAULT_FEATURE_COLUMNS,
    FeatureService,
    build_training_features,
)
from app.services.forecast_service import ForecastService
from app.services.history_provider import CsvHistoryProvider
from app.services.model_service import ModelService
from tests.artifact_factory import write_artifacts


def build_service(art) -> ForecastService:
    model = ModelService(
        model_path=art.model_path,
        model_config_path=art.artifacts_dir / "model_config.json",
        feature_columns_path=art.artifacts_dir / "feature_columns.json",
        metrics_path=art.artifacts_dir / "metrics.json",
        feature_importance_path=art.artifacts_dir / "feature_importance.csv",
    )
    model.load()
    return ForecastService(model, FeatureService(model.feature_columns), CsvHistoryProvider(art.history_path))


def test_24_and_168_hour_forecasts_are_finite(tmp_path):
    svc = build_service(write_artifacts(tmp_path))
    for horizon in (24, 168):
        result = svc.forecast("2026-01-15 00:00:00", horizon)
        assert len(result.points) == horizon
        assert np.isfinite([p.predicted_energy_kwh for p in result.points]).all()
        assert result.model == "StandInModel" and result.model_version == "v-test"


def test_first_step_matches_training_pipeline_prediction(tmp_path):
    """Serving parity: step 1 uses only real history, so it must equal the model
    applied to the vectorised training-style features for that hour."""
    art = write_artifacts(tmp_path)
    svc = build_service(art)
    origin = pd.Timestamp("2026-01-15 00:00:00")
    first = svc.forecast(origin, 3).points[0]
    training_rows = build_training_features(art.series, DEFAULT_FEATURE_COLUMNS)
    expected = art.model.predict(training_rows.loc[[first.timestamp]])[0]
    assert first.predicted_energy_kwh == pytest.approx(expected)


def test_later_steps_depend_on_earlier_predictions_not_actuals(tmp_path):
    """Forecasting from an earlier origin must differ from using actuals for step 2+."""
    art = write_artifacts(tmp_path)
    svc = build_service(art)
    origin = pd.Timestamp("2026-01-15 00:00:00")
    points = svc.forecast(origin, 2).points
    training_rows = build_training_features(art.series, DEFAULT_FEATURE_COLUMNS)
    actual_feature_pred = art.model.predict(training_rows.loc[[points[1].timestamp]])[0]
    # Step 2's lag_1 is the step-1 prediction (not the actual), so values differ slightly.
    assert abs(points[1].predicted_energy_kwh - actual_feature_pred) > 1e-9


def test_earliest_supported_origin_boundary(tmp_path):
    svc = build_service(write_artifacts(tmp_path))
    start = pd.Timestamp("2026-01-01 00:00:00")
    assert len(svc.forecast(start + pd.Timedelta(hours=167), 1).points) == 1
    with pytest.raises(InsufficientHistoryError):
        svc.forecast(start + pd.Timedelta(hours=166), 1)


def test_history_after_origin_does_not_change_forecast(tmp_path):
    art = write_artifacts(tmp_path)
    a = build_service(art).forecast("2026-01-15 00:00:00", 24)
    df = pd.read_csv(art.history_path, parse_dates=["timestamp"])
    df.loc[df["timestamp"] > "2026-01-15 00:00:00", "energy_kwh_hourly"] = 12345.0
    df.to_csv(art.history_path, index=False)
    b = build_service(art).forecast("2026-01-15 00:00:00", 24)
    assert [p.predicted_energy_kwh for p in a.points] == [p.predicted_energy_kwh for p in b.points]
