from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import APIResponse
from app.security import create_access_token
from app.services.auth_service import authenticate_user, register_user

# This module defines the authentication API routes for the FastAPI application, including user registration, login, and retrieving the current user's information.
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Endpoint for user registration, which accepts a RegisterRequest, creates a new user in the database, and returns the user's information in the response.
@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)

# Endpoint for user login, which accepts a LoginRequest, authenticates the user, and returns a TokenResponse containing the access token and its expiration time.
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserResponse]:
    try:
        user = await register_user(db, request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return APIResponse(data=UserResponse.model_validate(user), error=None)


# Endpoint for user login, which accepts a LoginRequest, authenticates the user, and returns a TokenResponse containing the access token and its expiration time.
@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    user = await authenticate_user(db, request.email, request.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_response = TokenResponse(
        access_token=create_access_token(str(user.id)),
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )

    return APIResponse(data=token_response, error=None)


# Endpoint to retrieve the current authenticated user's information, which requires a valid JWT token and returns the user's details in the response.
@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserResponse]:
    return APIResponse(data=UserResponse.model_validate(current_user), error=None)
