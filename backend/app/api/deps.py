"""FastAPI dependency-injection helpers.

All route functions obtain their services through these dependencies so that
the construction logic (reading app.state) stays in one place.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request

from app.repositories.forecast_repository import ForecastRepository
from app.services.forecast_service import ForecastService
from app.services.model_service import ModelService


def get_model_service(request: Request) -> ModelService:
    """Return the ModelService stored in app.state, or 503 if not loaded."""
    service: ModelService | None = getattr(request.app.state, "model_service", None)
    if service is None or not service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Check /health for details.",
        )
    return service


def get_forecast_service(request: Request) -> ForecastService:
    """Return the ForecastService stored in app.state, or 503 if unavailable."""
    service: ForecastService | None = getattr(request.app.state, "forecast_service", None)
    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Forecast service is not available. Check /health for details.",
        )
    return service


def get_history_provider(request: Request):
    """Return the CsvHistoryProvider stored in app.state, or 503 if unavailable."""
    history = getattr(request.app.state, "history", None)
    if history is None:
        raise HTTPException(
            status_code=503,
            detail="History data is not available. Check /health for details.",
        )
    return history


def get_forecast_repository() -> ForecastRepository:
    """Return a new ForecastRepository instance (stateless)."""
    return ForecastRepository()
