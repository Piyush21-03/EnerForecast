"""Source of hourly historical observations used to build forecast features.

Contract for the hourly history CSV exported by the training notebook:
  columns: `timestamp` plus the hourly target column, which is
           `energy_kwh_hourly` (preferred) or `energy_kwh`.
  Timestamps must be unique, ascending and aligned to the hour.
  Hours without data may be absent or NaN; they are never filled here.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

import pandas as pd

from app.core.exceptions import HistoryUnavailableError, InvalidTimestampError
from app.services.feature_service import HOUR, validate_history

logger = logging.getLogger(__name__)

TARGET_COLUMN_CANDIDATES = ("energy_kwh_hourly", "energy_kwh")


class HistoryProvider(Protocol):
    def latest_timestamp(self) -> pd.Timestamp | None: ...

    def get_window(self, end: pd.Timestamp, hours: int) -> pd.Series:
        """Observations for the `hours` hours ending at `end` (inclusive).

        Only rows that exist are returned; gaps are left for the caller to detect.
        """
        ...


class InMemoryHistory:
    def __init__(self, series: pd.Series) -> None:
        validate_history(series)
        self._series = series.astype(float)

    def latest_timestamp(self) -> pd.Timestamp | None:
        valid = self._series.dropna()
        return None if valid.empty else valid.index[-1]

    def get_window(self, end: pd.Timestamp, hours: int) -> pd.Series:
        start = end - (hours - 1) * HOUR
        return self._series.loc[start:end].copy()


class CsvHistoryProvider(InMemoryHistory):
    """Loads the hourly CSV once into memory (tens of thousands of rows)."""

    def __init__(self, path: Path) -> None:
        path = Path(path)
        if not path.is_file():
            raise HistoryUnavailableError(f"Hourly history file not found: {path}")
        try:
            header = pd.read_csv(path, nrows=0).columns
            target = next((c for c in TARGET_COLUMN_CANDIDATES if c in header), None)
            if "timestamp" not in header or target is None:
                raise HistoryUnavailableError(
                    f"{path.name} must contain 'timestamp' and one of {TARGET_COLUMN_CANDIDATES}"
                )
            df = pd.read_csv(path, usecols=["timestamp", target], parse_dates=["timestamp"])
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            raise HistoryUnavailableError(f"Cannot read hourly history {path.name}: {exc}") from exc
        series = pd.Series(df[target].to_numpy(dtype=float), index=pd.DatetimeIndex(df["timestamp"]), name="energy_kwh")
        try:
            super().__init__(series)
        except InvalidTimestampError as exc:
            raise HistoryUnavailableError(f"Invalid hourly history {path.name}: {exc}") from exc
        logger.info("Hourly history loaded: %d rows from %s (target column %s)", len(series), path.name, target)
