"""History providers: load the hourly energy_kwh series used for feature building.

HistoryProvider is an abstract base class. CsvHistoryProvider reads the
preprocessed CSV file that the training notebook produced. The path is
resolved at construction time; the data is loaded lazily on first access.

CSV contract:
  - Must contain a `timestamp` column (parseable by pandas) and an
    `energy_kwh` column (float).
  - Timestamps should be tz-naive and hour-aligned.
  - Duplicate timestamps are dropped (first kept).
  - The series is sorted ascending before being stored.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from app.core.exceptions import ArtifactNotFoundError, InvalidArtifactError

logger = logging.getLogger(__name__)

_TIMESTAMP_COL = "timestamp"
_TARGET_COL = "energy_kwh"


class HistoryProvider(ABC):
    """Abstract interface for hourly energy history."""

    @abstractmethod
    def get_window(self, origin: pd.Timestamp, hours: int) -> pd.Series:
        """Return up to `hours` observations ending at (and including) `origin`.

        The returned Series has a DatetimeIndex, is sorted ascending, and
        contains only rows at or before `origin`.
        """

    @abstractmethod
    def add_point(self, timestamp: pd.Timestamp, energy_kwh: float) -> None:
        """Add a real-time observation to the history."""

    @abstractmethod
    def latest_timestamp(self) -> pd.Timestamp | None:
        """The most recent timestamp available in the history, or None if empty."""

    @abstractmethod
    def summary(self) -> dict:
        """Basic statistics for logging / metadata registration."""


class CsvHistoryProvider(HistoryProvider):
    """Loads energy history from the preprocessed hourly CSV file."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._series: pd.Series | None = None  # loaded lazily

    # ---------------------------------------------------------------- loading
    def _ensure_loaded(self) -> pd.Series:
        if self._series is not None:
            return self._series
        self._series = self._load()
        return self._series

    def _load(self) -> pd.Series:
        if not self._path.is_file():
            raise ArtifactNotFoundError(f"History CSV not found: {self._path}")
        try:
            df = pd.read_csv(self._path)
        except Exception as exc:
            raise InvalidArtifactError(f"Cannot read history CSV {self._path.name}: {exc}") from exc

        missing = [c for c in (_TIMESTAMP_COL, _TARGET_COL) if c not in df.columns]
        if missing:
            raise InvalidArtifactError(
                f"History CSV is missing column(s): {', '.join(missing)}. "
                f"Available: {list(df.columns)}"
            )

        try:
            df[_TIMESTAMP_COL] = pd.to_datetime(df[_TIMESTAMP_COL])
        except Exception as exc:
            raise InvalidArtifactError(f"Cannot parse '{_TIMESTAMP_COL}' column: {exc}") from exc

        # Remove timezone so the series is always tz-naive, matching the model contract.
        if df[_TIMESTAMP_COL].dt.tz is not None:
            df[_TIMESTAMP_COL] = df[_TIMESTAMP_COL].dt.tz_localize(None)

        df = df.drop_duplicates(subset=[_TIMESTAMP_COL], keep="first")
        df = df.sort_values(_TIMESTAMP_COL)

        series = pd.Series(
            df[_TARGET_COL].astype(float).values,
            index=pd.DatetimeIndex(df[_TIMESTAMP_COL].values),
            name=_TARGET_COL,
        )

        logger.info(
            "History loaded: %d rows, %s to %s",
            len(series),
            series.index[0] if len(series) else "—",
            series.index[-1] if len(series) else "—",
        )
        return series

    # --------------------------------------------------------------- interface
    def get_window(self, origin: pd.Timestamp, hours: int) -> pd.Series:
        """Return up to `hours` observations ending at `origin` (inclusive)."""
        s = self._ensure_loaded()
        end_mask = s.index <= origin
        subset = s[end_mask]
        if len(subset) > hours:
            subset = subset.iloc[-hours:]
        return subset.copy()

    def add_point(self, timestamp: pd.Timestamp, energy_kwh: float) -> None:
        """Add a real-time observation to the history."""
        self._ensure_loaded()
        
        timestamp = pd.Timestamp(timestamp)
        # Ensure timestamp is naive
        if timestamp.tz is not None:
            timestamp = timestamp.tz_localize(None)

        # Update in memory
        self._series.loc[timestamp] = energy_kwh
        self._series.sort_index(inplace=True)

        # Append to CSV
        try:
            line = f"\n{timestamp},{energy_kwh}"
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as exc:
            logger.error("Failed to append real-time point to %s: %s", self._path, exc)

    def latest_timestamp(self) -> pd.Timestamp | None:
        s = self._ensure_loaded()
        if s.empty:
            return None
        return s.index[-1]

    def summary(self) -> dict:
        s = self._ensure_loaded()
        return {
            "rows": len(s),
            "start": s.index[0] if not s.empty else None,
            "end": s.index[-1] if not s.empty else None,
        }
