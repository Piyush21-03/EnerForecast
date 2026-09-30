import numpy as np
import pandas as pd
import pytest

from app.core.exceptions import (
    FeatureMismatchError,
    ForecastComputationError,
    HistoryUnavailableError,
    InsufficientHistoryError,
    InvalidHorizonError,
    InvalidTimestampError,
    PersistenceError,
)
from app.services.feature_service import FeatureService
from app.services.forecast_service import ForecastService
from app.services.history_provider import CsvHistoryProvider, InMemoryHistory

COLUMNS = ["lag_1", "lag_24", "rolling_mean_3", "hour_sin"]


class FakeModel:
    """Stand-in for ModelService: prediction = lag_1 + 1, so recursion is observable."""

    feature_columns = COLUMNS

    def __init__(self, fn=None):
        self._fn = fn or (lambda df: df["lag_1"].to_numpy() + 1.0)

    def predict(self, frame):
        assert list(frame.columns) == COLUMNS
        return np.asarray(self._fn(frame), dtype=float)

    def get_model_info(self):
        return {"model_name": "FakeModel", "model_version": "v-test"}


class FakeRepo:
    def __init__(self, fail_save=False):
        self.saved, self.logs, self.fail_save = [], [], False
        self.fail_save = fail_save

    def save_forecasts(self, db, **kw):
        if self.fail_save:
            raise PersistenceError("db down")
        self.saved.append(kw)
        return len(kw["points"])

    def add_prediction_log(self, db, **kw):
        self.logs.append(kw)


def make_history(n=300, start="2026-01-01 00:00:00"):
    idx = pd.date_range(start, periods=n, freq="h")
    return pd.Series(np.arange(n, dtype=float), index=idx)


def make_service(history=None, model=None, repo=None):
    history = history if history is not None else InMemoryHistory(make_history())
    return ForecastService(model or FakeModel(), FeatureService(COLUMNS), history, repo)


ORIGIN = "2026-01-10 00:00:00"  # hour index 216 -> value 216.0


def test_forecast_returns_horizon_points_with_correct_timestamps():
    result = make_service().forecast(ORIGIN, 24)
    assert result.horizon == 24 and result.unit == "kWh" and result.model == "FakeModel"
    assert len(result.points) == 24
    assert result.points[0].timestamp == pd.Timestamp("2026-01-10 01:00:00")
    assert result.points[-1].timestamp == pd.Timestamp("2026-01-11 00:00:00")


def test_recursion_feeds_predictions_back_as_lags():
    values = [p.predicted_energy_kwh for p in make_service().forecast(ORIGIN, 5).points]
    # last actual at origin is 216 -> 217, 218, ... only if each prediction becomes the next lag_1
    assert values == [217.0, 218.0, 219.0, 220.0, 221.0]


def test_168_hour_horizon_supported():
    assert len(make_service().forecast(ORIGIN, 168).points) == 168


def test_future_actuals_after_origin_are_never_used():
    base = make_history()
    poisoned = base.copy()
    poisoned.loc[pd.Timestamp(ORIGIN) + pd.Timedelta(hours=1):] = 99999.0
    a = make_service(InMemoryHistory(base)).forecast(ORIGIN, 24)
    b = make_service(InMemoryHistory(poisoned)).forecast(ORIGIN, 24)
    assert [p.predicted_energy_kwh for p in a.points] == [p.predicted_energy_kwh for p in b.points]


def test_invalid_timestamp_and_horizon():
    svc = make_service()
    for bad in ("not a date", "2026-01-10 00:30:00", pd.Timestamp(ORIGIN, tz="UTC"), None):
        with pytest.raises(InvalidTimestampError):
            svc.forecast(bad, 24)
    for bad in (0, 169, -1, 24.0, True, "24"):
        with pytest.raises(InvalidHorizonError):
            svc.forecast(ORIGIN, bad)


def test_origin_after_last_history_raises():
    with pytest.raises(InsufficientHistoryError):
        make_service().forecast("2027-01-01 00:00:00", 24)


def test_not_enough_history_before_origin_raises():
    with pytest.raises(InsufficientHistoryError):
        make_service().forecast("2026-01-01 05:00:00", 24)  # lag_24 unavailable


def test_gap_in_recent_history_raises():
    hist = make_history()
    hist = hist.drop(pd.Timestamp("2026-01-09 20:00:00"))
    with pytest.raises(InsufficientHistoryError):
        make_service(InMemoryHistory(hist)).forecast(ORIGIN, 24)


def test_non_finite_prediction_rejected():
    svc = make_service(model=FakeModel(lambda df: df["lag_1"].to_numpy() * np.nan))
    with pytest.raises(ForecastComputationError):
        svc.forecast(ORIGIN, 3)


def test_feature_mismatch_between_feature_service_and_model():
    with pytest.raises(FeatureMismatchError):
        ForecastService(FakeModel(), FeatureService(["lag_24", "lag_1", "rolling_mean_3", "hour_sin"]), InMemoryHistory(make_history()))


def test_forecast_and_store_persists_and_logs_success():
    repo = FakeRepo()
    result = make_service(repo=repo).forecast_and_store(object(), ORIGIN, 24)
    assert len(repo.saved) == 1
    saved = repo.saved[0]
    assert saved["request_id"] == result.request_id and saved["horizon"] == 24
    assert saved["model_version"] == "v-test" and len(saved["points"]) == 24
    assert repo.logs[0]["status"] == "success" and repo.logs[0]["model_version"] == "v-test"


def test_input_error_is_logged_and_nothing_saved():
    repo = FakeRepo()
    with pytest.raises(InvalidHorizonError):
        make_service(repo=repo).forecast_and_store(object(), ORIGIN, 500)
    assert repo.saved == [] and repo.logs[0]["status"] == "error"


def test_database_failure_propagates():
    repo = FakeRepo(fail_save=True)
    with pytest.raises(PersistenceError):
        make_service(repo=repo).forecast_and_store(object(), ORIGIN, 24)
    assert repo.logs[0]["status"] == "error"


def test_csv_history_provider(tmp_path):
    hist = make_history(48)
    path = tmp_path / "hourly.csv"
    pd.DataFrame({"timestamp": hist.index, "energy_kwh_hourly": hist.to_numpy(), "extra": 1}).to_csv(path, index=False)
    prov = CsvHistoryProvider(path)
    assert prov.latest_timestamp() == hist.index[-1]
    window = prov.get_window(hist.index[-1], 5)
    assert len(window) == 5 and window.iloc[-1] == 47.0


def test_csv_history_falls_back_to_energy_kwh_column(tmp_path):
    hist = make_history(10)
    path = tmp_path / "h.csv"
    pd.DataFrame({"timestamp": hist.index, "energy_kwh": hist.to_numpy()}).to_csv(path, index=False)
    assert CsvHistoryProvider(path).latest_timestamp() == hist.index[-1]


def test_csv_history_errors(tmp_path):
    with pytest.raises(HistoryUnavailableError):
        CsvHistoryProvider(tmp_path / "missing.csv")
    bad = tmp_path / "bad.csv"
    pd.DataFrame({"timestamp": ["2026-01-01 00:00:00"], "other": [1.0]}).to_csv(bad, index=False)
    with pytest.raises(HistoryUnavailableError):
        CsvHistoryProvider(bad)
    dup = tmp_path / "dup.csv"
    pd.DataFrame({"timestamp": ["2026-01-01 00:00:00"] * 2, "energy_kwh": [1.0, 2.0]}).to_csv(dup, index=False)
    with pytest.raises(HistoryUnavailableError):
        CsvHistoryProvider(dup)
