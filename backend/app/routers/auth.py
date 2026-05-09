from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.limiter import limiter
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.common import APIResponse
from app.security import create_access_token
from app.services.auth_service import authenticate_user, register_user
from app.services.refresh_token_service import (
    InvalidRefreshTokenError,
    create_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserResponse]:
    try:
        user = await register_user(db, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed",
        ) from exc

    return APIResponse(data=UserResponse.model_validate(user), error=None)


@router.post("/login", response_model=APIResponse[TokenResponse])
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    user = await authenticate_user(db, body.email, body.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    refresh_raw = await create_refresh_token(db, user.id)

    token_response = TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=refresh_raw,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )

    return APIResponse(data=token_response, error=None)


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
@limiter.limit("10/minute")
async def token_for_swagger(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await authenticate_user(db, form_data.username, form_data.password)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    refresh_raw = await create_refresh_token(db, user.id)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=refresh_raw,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserResponse]:
    return APIResponse(data=UserResponse.model_validate(current_user), error=None)


@router.post("/refresh", response_model=APIResponse[TokenResponse])
@limiter.limit("10/minute")
async def refresh(
    request: Request,
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    try:
        user, new_refresh_raw = await rotate_refresh_token(db, body.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    token_response = TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=new_refresh_raw,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )

    return APIResponse(data=token_response, error=None)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    db: AsyncSession = Depends(get_db),
) -> Response:
    await revoke_refresh_token(db, body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
