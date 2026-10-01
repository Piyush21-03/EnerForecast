"""Global exception handlers for the FastAPI application.

Registers handlers that convert domain-specific exceptions into well-formed
HTTP JSON responses. All handlers log at appropriate levels so errors are
visible in the application logs.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ForecastComputationError,
    ForecastInputError,
    ModelArtifactError,
    ModelNotLoadedError,
    PersistenceError,
)

logger = logging.getLogger(__name__)


def _error_body(message: str) -> dict:
    return {"detail": message}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all domain-exception handlers to *app*."""

    @app.exception_handler(ForecastInputError)
    async def forecast_input_error_handler(request: Request, exc: ForecastInputError) -> JSONResponse:
        logger.info("Forecast input error on %s: %s", request.url.path, exc)
        return JSONResponse(status_code=422, content=_error_body(str(exc)))

    @app.exception_handler(ForecastComputationError)
    async def forecast_computation_error_handler(
        request: Request, exc: ForecastComputationError
    ) -> JSONResponse:
        logger.error("Forecast computation error on %s: %s", request.url.path, exc)
        return JSONResponse(status_code=500, content=_error_body(str(exc)))

    @app.exception_handler(ModelNotLoadedError)
    async def model_not_loaded_handler(request: Request, exc: ModelNotLoadedError) -> JSONResponse:
        logger.warning("Model not loaded for %s: %s", request.url.path, exc)
        return JSONResponse(status_code=503, content=_error_body(str(exc)))

    @app.exception_handler(ModelArtifactError)
    async def model_artifact_error_handler(request: Request, exc: ModelArtifactError) -> JSONResponse:
        logger.error("Model artifact error on %s: %s", request.url.path, exc)
        return JSONResponse(status_code=503, content=_error_body(str(exc)))

    @app.exception_handler(PersistenceError)
    async def persistence_error_handler(request: Request, exc: PersistenceError) -> JSONResponse:
        logger.error("Persistence error on %s: %s", request.url.path, exc)
        return JSONResponse(status_code=503, content=_error_body(str(exc)))
