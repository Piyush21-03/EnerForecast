from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_forecast_service
from app.core.exceptions import ForecastComputationError, ForecastInputError
from app.db.database import get_db
from app.models.schemas import (
    BatchPredictItem,
    BatchPredictRequest,
    BatchPredictResponse,
    ForecastPointSchema,
    PredictRequest,
    PredictResponse,
)
from app.services.forecast_service import ForecastResult, ForecastService

router = APIRouter(tags=["forecast"])


def to_predict_response(result: ForecastResult) -> PredictResponse:
    return PredictResponse(
        request_id=result.request_id,
        model=result.model,
        model_version=result.model_version,
        horizon=result.horizon,
        unit=result.unit,
        forecast_timestamp=result.origin.to_pydatetime(),
        forecast=[
            ForecastPointSchema(timestamp=p.timestamp.to_pydatetime(), predicted_energy_kwh=p.predicted_energy_kwh)
            for p in result.points
        ],
    )


@router.post("/predict", response_model=PredictResponse)
def predict(
    body: PredictRequest,
    db: Session = Depends(get_db),
    service: ForecastService = Depends(get_forecast_service),
) -> PredictResponse:
    result = service.forecast_and_store(db, body.timestamp, body.horizon, endpoint="/predict")
    return to_predict_response(result)


@router.post("/batch-predict", response_model=BatchPredictResponse)
def batch_predict(
    body: BatchPredictRequest,
    db: Session = Depends(get_db),
    service: ForecastService = Depends(get_forecast_service),
) -> BatchPredictResponse:
    """Runs each request independently; a bad item does not fail the others.
    Database failures still abort the whole call (503)."""
    items: list[BatchPredictItem] = []
    for index, req in enumerate(body.requests):
        try:
            result = service.forecast_and_store(db, req.timestamp, req.horizon, endpoint="/batch-predict")
            items.append(BatchPredictItem(index=index, success=True, result=to_predict_response(result)))
        except (ForecastInputError, ForecastComputationError) as exc:
            items.append(BatchPredictItem(index=index, success=False, error=f"{type(exc).__name__}: {exc}"))
    return BatchPredictResponse(results=items)
