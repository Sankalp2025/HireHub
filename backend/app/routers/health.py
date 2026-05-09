from fastapi import APIRouter
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
async def health_check() -> APIResponse[HealthData]:
    # Connects to the database and checks if it's responsive
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return APIResponse(
        data=HealthData(
            status="ok",
            db=db_status,
            analysis_engine="ready",
        ),
        error=None,
    )
