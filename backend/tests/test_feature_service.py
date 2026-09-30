import math

import numpy as np
import pandas as pd
import pytest

from app.core.exceptions import (
    FeatureMismatchError,
    InsufficientHistoryError,
    InvalidTimestampError,
)
from app.services.feature_service import (
    DEFAULT_FEATURE_COLUMNS,
    FeatureService,
    build_training_features,
    validate_history,
)


def make_history(n=400, start="2026-01-01 00:00:00", seed=0) -> pd.Series:
    idx = pd.date_range(start, periods=n, freq="h")
    return pd.Series(np.random.default_rng(seed).random(n) * 5, index=idx, name="energy_kwh")


def test_default_feature_columns_are_supported_and_unique():
    svc = FeatureService(DEFAULT_FEATURE_COLUMNS)
    assert svc.required_lookback_hours == 168
    assert len(set(DEFAULT_FEATURE_COLUMNS)) == len(DEFAULT_FEATURE_COLUMNS)


def test_calendar_and_cyclical_values():
    svc = FeatureService(["hour", "day_of_week", "is_weekend", "week_of_year", "hour_sin", "day_of_week_cos"])
    wed = svc.build_row(make_history(), "2026-09-30 10:00:00")  # a Wednesday
    assert wed["hour"] == 10 and wed["day_of_week"] == 2 and wed["is_weekend"] == 0
    assert wed["week_of_year"] == 40
    assert wed["hour_sin"] == pytest.approx(math.sin(2 * math.pi * 10 / 24))
    assert wed["day_of_week_cos"] == pytest.approx(math.cos(2 * math.pi * 2 / 7))
    sat = svc.build_row(make_history(), "2026-10-03 00:00:00")
    assert sat["is_weekend"] == 1


def test_row_builder_matches_vectorised_training_features():
    hist = make_history()
    svc = FeatureService(DEFAULT_FEATURE_COLUMNS)
    vec = build_training_features(hist, DEFAULT_FEATURE_COLUMNS)
    for ts in hist.index[168::37]:
        row = svc.build_row(hist, ts)
        expected = vec.loc[ts]
        for name in DEFAULT_FEATURE_COLUMNS:
            assert row[name] == pytest.approx(float(expected[name])), (ts, name)


def test_no_target_leakage():
    hist = make_history()
    svc = FeatureService(DEFAULT_FEATURE_COLUMNS)
    ts = hist.index[300]
    base = svc.build_row(hist, ts)

    changed = hist.copy()
    changed.iloc[300:] = 999.0  # target at t and everything after
    assert svc.build_row(changed, ts) == base

    changed = hist.copy()
    changed.iloc[299] = 999.0  # t-1 must matter
    assert svc.build_row(changed, ts)["lag_1"] == 999.0


def test_recursive_style_use_of_predictions_as_history():
    hist = make_history()
    svc = FeatureService(["lag_1", "lag_2", "rolling_mean_3"])
    t1 = hist.index[-1] + pd.Timedelta(hours=1)
    extended = pd.concat([hist, pd.Series([7.0], index=[t1])])
    row = svc.build_row(extended, t1 + pd.Timedelta(hours=1))
    assert row["lag_1"] == 7.0
    assert row["lag_2"] == hist.iloc[-1]


def test_insufficient_history_raises():
    with pytest.raises(InsufficientHistoryError):
        FeatureService(["lag_168"]).build_row(make_history(100), "2026-01-05 05:00:00")


def test_gap_in_history_is_not_filled():
    hist = make_history().drop(make_history().index[250])
    svc = FeatureService(["rolling_mean_24"])
    with pytest.raises(InsufficientHistoryError):
        svc.build_row(hist, hist.index[260])


def test_unsupported_or_duplicate_features_rejected():
    with pytest.raises(FeatureMismatchError):
        FeatureService(["lag_1", "Voltage"])
    with pytest.raises(FeatureMismatchError):
        FeatureService(["lag_1", "lag_1"])


def test_optional_lags_supported():
    svc = FeatureService(["lag_336"])
    assert svc.required_lookback_hours == 336


def test_build_frame_column_order_matches_feature_columns():
    hist = make_history()
    cols = ["hour_sin", "lag_24", "rolling_std_6", "lag_1"]
    frame = FeatureService(cols).build_frame(hist, hist.index[200:203])
    assert list(frame.columns) == cols and len(frame) == 3


def test_target_timestamp_must_be_hour_aligned_and_naive():
    svc = FeatureService(["lag_1"])
    with pytest.raises(InvalidTimestampError):
        svc.build_row(make_history(), "2026-01-05 05:30:00")
    with pytest.raises(InvalidTimestampError):
        svc.build_row(make_history(), pd.Timestamp("2026-01-05 05:00:00", tz="UTC"))


def test_validate_history_rejects_bad_series():
    good = make_history(10)
    validate_history(good)
    with pytest.raises(InvalidTimestampError):
        validate_history(good.iloc[::-1])
    with pytest.raises(InvalidTimestampError):
        validate_history(pd.concat([good, good.iloc[:1]]))
    with pytest.raises(InvalidTimestampError):
        validate_history(pd.Series([1.0], index=pd.to_datetime(["2026-01-01 00:30:00"])))
    with pytest.raises(InvalidTimestampError):
        validate_history(good.tz_localize("UTC"))
