from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.security import generate_refresh_token, hash_refresh_token


class InvalidRefreshTokenError(ValueError):
    pass


async def create_refresh_token(db: AsyncSession, user_id: UUID) -> str:
    raw, hashed = generate_refresh_token()
    token = RefreshToken(
        user_id=user_id,
        token_hash=hashed,
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(token)
    await db.commit()
    return raw


async def rotate_refresh_token(
    db: AsyncSession,
    raw_token: str,
) -> tuple[User, str]:
    hashed = hash_refresh_token(raw_token)
    stmt = (
        select(RefreshToken)
        .where(RefreshToken.token_hash == hashed)
        .with_for_update()
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()

    if token is None or token.revoked_at is not None:
        raise InvalidRefreshTokenError("Invalid refresh token")

    if token.expires_at < datetime.now(UTC):
        raise InvalidRefreshTokenError("Refresh token expired")

    user_stmt = select(User).where(User.id == token.user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise InvalidRefreshTokenError("Invalid refresh token")

    token.revoked_at = datetime.now(UTC)

    new_raw, new_hashed = generate_refresh_token()
    new_token = RefreshToken(
        user_id=user.id,
        token_hash=new_hashed,
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(new_token)
    await db.commit()
    return user, new_raw


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> None:
    hashed = hash_refresh_token(raw_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed)
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()

    if token is not None and token.revoked_at is None:
        token.revoked_at = datetime.now(UTC)
        await db.commit()
