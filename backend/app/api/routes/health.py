from fastapi import APIRouter, Request
from sqlalchemy import text

from app.db.database import get_engine
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


def check_database() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # any failure means "not healthy"; details are in logs elsewhere
        return False


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    model_service = getattr(request.app.state, "model_service", None)
    model_loaded = bool(model_service and model_service.is_loaded)
    history_loaded = getattr(request.app.state, "forecast_service", None) is not None
    database_ok = check_database()
    ok = model_loaded and history_loaded and database_ok
    return HealthResponse(
        status="ok" if ok else "degraded",
        model_loaded=model_loaded,
        history_loaded=history_loaded,
        database_ok=database_ok,
    )
