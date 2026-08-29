from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text

from app.database import engine
from app.schemas.common import APIResponse

# Create a router for health check endpoints
router = APIRouter(prefix="/api/v1", tags=["health"])


class HealthData(BaseModel):
    status: str
    db: str
    analysis_engine: str


@router.get("/health", response_model=APIResponse[HealthData])
async def health_check(response: Response) -> APIResponse[HealthData]:
    # Connects to the database and checks if it's responsive
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        db_status = "connected"
        service_status = "ok"
    except Exception:
        db_status = "disconnected"
        service_status = "unavailable"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return APIResponse(
        data=HealthData(
            status=service_status,
            db=db_status,
            analysis_engine="ready",
        ),
        error=None,
    )
