from fastapi import APIRouter
from sqlalchemy import text

from app.database import engine

# Create a router for health check endpoints
router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    
    # Connects to the database and checks if it's responsive
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            
        db_status = "connected"
        
    except Exception:
        db_status = "disconnected"

    return {
        "data": {
            "status": "ok",
            "db": db_status,
            "analysis_engine": "ready",
        },
        "error": None,
    }
