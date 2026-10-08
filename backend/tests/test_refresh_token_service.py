from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.auth_service import register_user
from app.services.refresh_token_service import (
    InvalidRefreshTokenError,
    create_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)
from tests.conftest import TestSessionLocal


@pytest.fixture
async def db() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def user(db: AsyncSession) -> User:
    request = RegisterRequest(
        email="token@example.com", password="password123", full_name="Token User"
    )
    return await register_user(db, request)


async def test_create_refresh_token_returns_raw_string(db: AsyncSession, user: User):
    raw = await create_refresh_token(db, user.id)
    assert isinstance(raw, str)
    assert len(raw) > 0


async def test_create_refresh_token_is_stored_hashed(db: AsyncSession, user: User):
    raw = await create_refresh_token(db, user.id)
    result = await db.execute(select(RefreshToken).where(RefreshToken.user_id == user.id))
    token = result.scalar_one()
    assert token.token_hash != raw


async def test_rotate_refresh_token_returns_new_raw_token(db: AsyncSession, user: User):
    raw = await create_refresh_token(db, user.id)
    returned_user, new_raw = await rotate_refresh_token(db, raw)
    assert returned_user.id == user.id
    assert new_raw != raw
    assert len(new_raw) > 0


async def test_rotate_revokes_old_token(db: AsyncSession, user: User):
    raw = await create_refresh_token(db, user.id)
    from app.security import hash_refresh_token

    old_hash = hash_refresh_token(raw)

    await rotate_refresh_token(db, raw)

    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == old_hash))
    old_token = result.scalar_one()
    assert old_token.revoked_at is not None


async def test_rotate_invalid_token_raises(db: AsyncSession):
    with pytest.raises(InvalidRefreshTokenError):
        await rotate_refresh_token(db, "not-a-real-token")


async def test_rotate_already_revoked_token_raises(db: AsyncSession, user: User):
    raw = await create_refresh_token(db, user.id)
    await rotate_refresh_token(db, raw)
    with pytest.raises(InvalidRefreshTokenError):
        await rotate_refresh_token(db, raw)


async def test_rotate_expired_token_raises(db: AsyncSession, user: User):
    raw = await create_refresh_token(db, user.id)
    from app.security import hash_refresh_token

    hashed = hash_refresh_token(raw)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hashed))
    token = result.scalar_one()
    token.expires_at = datetime.now(UTC) - timedelta(days=1)
    await db.commit()

    with pytest.raises(InvalidRefreshTokenError):
        await rotate_refresh_token(db, raw)


async def test_rotate_inactive_user_token_raises(db: AsyncSession, user: User):
    raw = await create_refresh_token(db, user.id)
    user.is_active = False
    await db.commit()

    with pytest.raises(InvalidRefreshTokenError):
        await rotate_refresh_token(db, raw)


async def test_revoke_refresh_token_marks_revoked(db: AsyncSession, user: User):
    raw = await create_refresh_token(db, user.id)
    await revoke_refresh_token(db, raw)

    from app.security import hash_refresh_token

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw))
    )
    token = result.scalar_one()
    assert token.revoked_at is not None


async def test_revoke_nonexistent_token_is_silent(db: AsyncSession):
    await revoke_refresh_token(db, "does-not-exist")
