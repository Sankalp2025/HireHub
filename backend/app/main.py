from fastapi import FastAPI

from app.routers import analyses, auth, health, job_descriptions, resumes

# Initialize the FastAPI application
app = FastAPI(title="HireHub API", version="0.1.0")

# Include the routers for health checks, authentication, and resume management in the application
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(job_descriptions.router)
app.include_router(analyses.router)
