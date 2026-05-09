import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.limiter import limiter
from app.routers import analyses, auth, health, job_descriptions, resumes
from app.schemas.common import APIError, APIResponse

logger = logging.getLogger(__name__)

# Initialize the FastAPI application
app = FastAPI(title="HireHub API", version="0.1.0")

# Attach the shared rate-limiter so slowapi can find it via app.state.
app.state.limiter = limiter

# Allow the configured frontend origins to call the API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SlowAPI middleware provides rate-limit integration for decorated endpoints.
app.add_middleware(SlowAPIMiddleware)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    headers: dict | None = None,
) -> JSONResponse:
    body = APIResponse[None](data=None, error=APIError(code=code, message=message))
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers=headers,
    )


# Reshape FastAPI's default {"detail": ...} errors into the standard
# {"data": null, "error": {...}} envelope used by successful responses.
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        code=f"http_{exc.status_code}",
        message=str(exc.detail) if exc.detail is not None else "",
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Compact summary; the envelope only carries a single message field.
    errors = exc.errors()
    if errors:
        first = errors[0]
        loc = ".".join(str(p) for p in first.get("loc", ()))
        msg = first.get("msg", "invalid input")
        message = f"{loc}: {msg}" if loc else msg
    else:
        message = "Invalid request"
    return _error_response(status_code=422, code="validation_error", message=message)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return _error_response(
        status_code=429,
        code="rate_limit_exceeded",
        message="Too many requests — please slow down and try again shortly.",
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return _error_response(status_code=500, code="internal_error", message="Internal server error")


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(job_descriptions.router)
app.include_router(analyses.router)
