from fastapi import FastAPI

from app.routers import health

# Initialize the FastAPI application
app = FastAPI(title="HireHub API", version="0.1.0")

# Include the health check router
app.include_router(health.router)
