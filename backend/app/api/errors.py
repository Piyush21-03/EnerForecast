"""Maps domain exceptions to HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ForecastInputError,
    ForecastServiceError,
    HistoryUnavailableError,
    ModelArtifactError,
    ModelNotLoadedError,
    PersistenceError,
)


def _response(status_code: int, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": str(exc), "error": type(exc).__name__})


def register_exception_handlers(app: FastAPI) -> None:
    # Starlette picks the most specific handler by class hierarchy.
    @app.exception_handler(ForecastInputError)
    async def _input_error(request: Request, exc: ForecastInputError) -> JSONResponse:
        return _response(422, exc)

    @app.exception_handler(ModelNotLoadedError)
    async def _not_loaded(request: Request, exc: ModelNotLoadedError) -> JSONResponse:
        return _response(503, exc)

    @app.exception_handler(HistoryUnavailableError)
    async def _history_unavailable(request: Request, exc: HistoryUnavailableError) -> JSONResponse:
        return _response(503, exc)

    @app.exception_handler(PersistenceError)
    async def _persistence(request: Request, exc: PersistenceError) -> JSONResponse:
        return _response(503, exc)

    @app.exception_handler(ModelArtifactError)
    async def _artifact_error(request: Request, exc: ModelArtifactError) -> JSONResponse:
        return _response(500, exc)

    @app.exception_handler(ForecastServiceError)
    async def _service_error(request: Request, exc: ForecastServiceError) -> JSONResponse:
        return _response(500, exc)
