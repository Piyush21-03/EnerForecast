"""Feature generation for inference.

This module is the single source of truth for feature logic. The training
notebook must use the same definitions (copy `build_training_features` and
`DEFAULT_FEATURE_COLUMNS` verbatim) so training and production cannot drift.

Conventions (all on the HOURLY series of the target `energy_kwh`):
  lag_k              value at t - k hours
  rolling_mean_w     mean of the w values at t-w .. t-1   (target shifted by 1)
  rolling_std_w      sample std (ddof=1) of the same w values
  hour, day_of_month, day_of_week (Mon=0), month, week_of_year (ISO), is_weekend
  hour_sin/cos       sin/cos(2*pi*hour/24)
  day_of_week_sin/cos  sin/cos(2*pi*day_of_week/7)

The target at time t is never used to build features for time t. Missing
history is never filled: it raises InsufficientHistoryError.
Exogenous variables (Voltage, Sub_metering_*, ...) are not used: their future
values are unknown at forecast time.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Sequence

import numpy as np
import pandas as pd

from app.core.exceptions import (
    FeatureMismatchError,
    InsufficientHistoryError,
    InvalidTimestampError,
)

HOUR = pd.Timedelta(hours=1)

LAGS = (1, 2, 3, 24, 48, 168)
ROLLING_WINDOWS = (3, 6, 24, 168)
CALENDAR_FEATURES = ("hour", "day_of_month", "day_of_week", "month", "week_of_year", "is_weekend")
CYCLICAL_FEATURES = ("hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos")

DEFAULT_FEATURE_COLUMNS: list[str] = (
    [f"lag_{k}" for k in LAGS]
    + [f"rolling_mean_{w}" for w in ROLLING_WINDOWS]
    + [f"rolling_std_{w}" for w in ROLLING_WINDOWS]
    + list(CALENDAR_FEATURES)
    + list(CYCLICAL_FEATURES)
)

_LAG_RE = re.compile(r"^lag_(\d+)$")
_MEAN_RE = re.compile(r"^rolling_mean_(\d+)$")
_STD_RE = re.compile(r"^rolling_std_(\d+)$")


def _lookback_of(name: str) -> int:
    """Hours of history a feature needs (0 for calendar features). Raises if unsupported."""
    for regex in (_LAG_RE, _MEAN_RE, _STD_RE):
        m = regex.match(name)
        if m:
            n = int(m.group(1))
            if n < 1:
                break
            return n
    if name in CALENDAR_FEATURES or name in CYCLICAL_FEATURES:
        return 0
    raise FeatureMismatchError(f"Unsupported feature in feature_columns.json: {name!r}")


def _calendar_values(ts: pd.Timestamp) -> dict[str, float]:
    dow = ts.dayofweek
    return {
        "hour": ts.hour,
        "day_of_month": ts.day,
        "day_of_week": dow,
        "month": ts.month,
        "week_of_year": int(ts.isocalendar()[1]),
        "is_weekend": int(dow >= 5),
        "hour_sin": math.sin(2 * math.pi * ts.hour / 24),
        "hour_cos": math.cos(2 * math.pi * ts.hour / 24),
        "day_of_week_sin": math.sin(2 * math.pi * dow / 7),
        "day_of_week_cos": math.cos(2 * math.pi * dow / 7),
    }


def validate_history(history: pd.Series) -> None:
    """History must be a sorted, unique, tz-naive, hour-aligned series."""
    idx = history.index
    if not isinstance(idx, pd.DatetimeIndex):
        raise InvalidTimestampError("History must be indexed by timestamp")
    if idx.tz is not None:
        raise InvalidTimestampError("History timestamps must be timezone-naive")
    if idx.has_duplicates:
        raise InvalidTimestampError("History contains duplicate timestamps")
    if not idx.is_monotonic_increasing:
        raise InvalidTimestampError("History timestamps must be sorted ascending")
    if len(idx) and ((idx.minute != 0).any() or (idx.second != 0).any() or (idx.microsecond != 0).any()):
        raise InvalidTimestampError("History timestamps must be aligned to the hour")


def _check_target_timestamp(ts: pd.Timestamp) -> pd.Timestamp:
    ts = pd.Timestamp(ts)
    if ts.tzinfo is not None:
        raise InvalidTimestampError("Timestamps must be timezone-naive")
    if ts != ts.floor("h"):
        raise InvalidTimestampError(f"Timestamp {ts} is not aligned to the hour")
    return ts


class FeatureService:
    def __init__(self, feature_columns: Sequence[str]) -> None:
        self.feature_columns = list(feature_columns)
        if not self.feature_columns or len(set(self.feature_columns)) != len(self.feature_columns):
            raise FeatureMismatchError("feature_columns must be a non-empty list of unique names")
        self._lookbacks = {name: _lookback_of(name) for name in self.feature_columns}
        self.required_lookback_hours = max(self._lookbacks.values())

    def build_row(self, history: pd.Series, timestamp: pd.Timestamp | str) -> dict[str, float]:
        """Features for one target hour, using only history strictly before it.

        `history` may already contain earlier predictions (recursive forecasting).
        Values at or after `timestamp` are ignored.
        """
        ts = _check_target_timestamp(timestamp)
        row: dict[str, float] = {}
        cal = _calendar_values(ts)

        window = np.empty(0)
        if self.required_lookback_hours:
            index = pd.date_range(end=ts - HOUR, periods=self.required_lookback_hours, freq=HOUR)
            window = history.reindex(index).to_numpy(dtype=float)  # oldest -> newest (t-1)

        for name in self.feature_columns:
            n = self._lookbacks[name]
            if n == 0:
                row[name] = cal[name]
            elif name.startswith("lag_"):
                value = window[-n]
                if np.isnan(value):
                    raise self._missing(ts, name, n)
                row[name] = float(value)
            else:
                chunk = window[-n:]
                if np.isnan(chunk).any():
                    raise self._missing(ts, name, n)
                if name.startswith("rolling_mean_"):
                    row[name] = float(chunk.mean())
                else:
                    row[name] = float(chunk.std(ddof=1)) if n > 1 else float("nan")
        return row

    def build_frame(self, history: pd.Series, timestamps: Iterable[pd.Timestamp | str]) -> pd.DataFrame:
        """Feature matrix (columns in feature_columns order) for known-history rows.

        Not recursive: every row must be fully supported by `history`.
        """
        validate_history(history)
        rows = [self.build_row(history, ts) for ts in timestamps]
        return pd.DataFrame(rows, columns=self.feature_columns)

    @staticmethod
    def _missing(ts: pd.Timestamp, name: str, hours: int) -> InsufficientHistoryError:
        start = ts - hours * HOUR
        return InsufficientHistoryError(
            f"Insufficient contiguous hourly history for {name} at {ts}: "
            f"need every hour from {start} to {ts - HOUR}"
        )


def build_training_features(series: pd.Series, feature_columns: Sequence[str]) -> pd.DataFrame:
    """Vectorised equivalent of FeatureService.build_row over a whole series.

    This is what the Colab notebook should use. The series is first placed on a
    continuous hourly grid so shifts are time-based, exactly like build_row;
    gaps become NaN and are never filled. Rows with NaN features must be
    dropped by the caller before training.
    """
    validate_history(series)
    if series.empty:
        return pd.DataFrame(columns=list(feature_columns))
    grid = pd.date_range(series.index[0], series.index[-1], freq=HOUR)
    s = series.reindex(grid).astype(float)
    shifted = s.shift(1)  # target shifted before any rolling: no leakage
    idx = s.index
    out: dict[str, pd.Series | np.ndarray] = {}
    calendar = {
        "hour": idx.hour,
        "day_of_month": idx.day,
        "day_of_week": idx.dayofweek,
        "month": idx.month,
        "week_of_year": idx.isocalendar().week.to_numpy(),
        "is_weekend": (idx.dayofweek >= 5).astype(int),
        "hour_sin": np.sin(2 * np.pi * idx.hour / 24),
        "hour_cos": np.cos(2 * np.pi * idx.hour / 24),
        "day_of_week_sin": np.sin(2 * np.pi * idx.dayofweek / 7),
        "day_of_week_cos": np.cos(2 * np.pi * idx.dayofweek / 7),
    }
    for name in feature_columns:
        n = _lookback_of(name)
        if n == 0:
            out[name] = np.asarray(calendar[name], dtype=float)
        elif name.startswith("lag_"):
            out[name] = s.shift(n).to_numpy()
        elif name.startswith("rolling_mean_"):
            out[name] = shifted.rolling(n).mean().to_numpy()
        else:
            out[name] = shifted.rolling(n).std().to_numpy()
    return pd.DataFrame(out, index=idx, columns=list(feature_columns))
