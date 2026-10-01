from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_forecast_repository
from app.db.database import get_db
from app.models.schemas import ForecastHistoryItem, ForecastHistoryResponse
from app.repositories.forecast_repository import ForecastRepository

router = APIRouter(tags=["history"])


@router.get("/forecast-history", response_model=ForecastHistoryResponse)
def forecast_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Literal["created_at", "prediction_timestamp", "predicted_energy_kwh", "horizon"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    date_from: date | None = Query(None, description="Include forecasts created on/after this date"),
    date_to: date | None = Query(None, description="Include forecasts created on/before this date"),
    db: Session = Depends(get_db),
    repo: ForecastRepository = Depends(get_forecast_repository),
) -> ForecastHistoryResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must not be after date_to")
    rows, total = repo.list_forecasts(
        db, page=page, page_size=page_size, sort_by=sort_by, order=order, date_from=date_from, date_to=date_to
    )
    return ForecastHistoryResponse(
        items=[ForecastHistoryItem.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
