"""Energy history routes.

Exposes the raw CSV history for the dashboard:
  GET /energy/latest  – the most recent hourly reading
  GET /energy/history – paginated/aggregated readings (hourly, daily, weekly)
"""

from __future__ import annotations

import logging
from typing import Literal

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_history_provider
from app.models.schemas import EnergyHistoryPoint, EnergyHistoryResponse, LatestEnergyResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/energy", tags=["energy"])


@router.get("/latest", response_model=LatestEnergyResponse)
def latest_energy(history=Depends(get_history_provider)) -> LatestEnergyResponse:
    """Return the most recent hourly energy reading from the history CSV."""
    ts = history.latest_timestamp()
    if ts is None:
        raise HTTPException(status_code=404, detail="No history data available")
    window = history.get_window(ts, hours=1)
    if window.empty:
        raise HTTPException(status_code=404, detail="No history data available")
    return LatestEnergyResponse(
        timestamp=ts.to_pydatetime(),
        energy_kwh=float(window.iloc[-1]),
        unit="kWh",
    )


@router.get("/history", response_model=EnergyHistoryResponse)
def energy_history(
    aggregate: Literal["hourly", "daily", "weekly"] = Query(
        "daily", description="Aggregation level for returned points"
    ),
    limit: int = Query(168, ge=1, le=8760, description="Maximum number of points to return"),
    history=Depends(get_history_provider),
) -> EnergyHistoryResponse:
    """Return aggregated energy history suitable for charting."""
    latest = history.latest_timestamp()
    if latest is None:
        return EnergyHistoryResponse(aggregate=aggregate, unit="kWh", points=[])

    # Pull a large window: weekly -> up to 2 years of hourly data, daily -> 1 year, hourly -> 30 days
    lookback_hours = {"hourly": 720, "daily": 8760, "weekly": 17520}[aggregate]
    series = history.get_window(latest, hours=lookback_hours)

    if series.empty:
        return EnergyHistoryResponse(aggregate=aggregate, unit="kWh", points=[])

    freq_map = {"hourly": "h", "daily": "D", "weekly": "W"}
    resample_freq = freq_map[aggregate]

    resampled = series.resample(resample_freq).agg(["sum", "count"])
    resampled.columns = ["energy_kwh", "hours"]
    resampled = resampled[resampled["hours"] > 0].dropna()

    # Most-recent first, then trim to limit
    resampled = resampled.iloc[-limit:]

    points = [
        EnergyHistoryPoint(
            timestamp=row.Index.to_pydatetime(),
            energy_kwh=float(row.energy_kwh),
            hours=int(row.hours),
        )
        for row in resampled.itertuples()
    ]

    return EnergyHistoryResponse(aggregate=aggregate, unit="kWh", points=points)
