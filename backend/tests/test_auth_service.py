import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import RegisterRequest
from app.services.auth_service import authenticate_user, get_user_by_email, register_user
from tests.conftest import TestSessionLocal


@pytest.fixture
async def db() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


async def test_register_user_persists_and_returns_user(db: AsyncSession):
    request = RegisterRequest(email="reg@example.com", password="password123", full_name="Reg User")
    user = await register_user(db, request)

    assert user.id is not None
    assert user.email == "reg@example.com"
    assert user.full_name == "Reg User"
    assert user.is_active is True
    assert user.hashed_password != "password123"


async def test_register_user_normalizes_email(db: AsyncSession):
    request = RegisterRequest(email="Mixed@EXAMPLE.COM", password="password123", full_name="Mixed")
    user = await register_user(db, request)
    assert user.email == "mixed@example.com"


async def test_register_user_strips_full_name_whitespace(db: AsyncSession):
    request = RegisterRequest(
        email="trim@example.com", password="password123", full_name="  Trim User  "
    )
    user = await register_user(db, request)
    assert user.full_name == "Trim User"


async def test_register_duplicate_email_raises(db: AsyncSession):
    request = RegisterRequest(email="dup@example.com", password="password123", full_name="Dup")
    await register_user(db, request)
    with pytest.raises(ValueError, match="already registered"):
        await register_user(db, request)


async def test_get_user_by_email_returns_user(db: AsyncSession):
    request = RegisterRequest(email="find@example.com", password="password123", full_name="Find")
    await register_user(db, request)
    user = await get_user_by_email(db, "find@example.com")
    assert user is not None
    assert user.email == "find@example.com"


async def test_get_user_by_email_is_case_insensitive(db: AsyncSession):
    request = RegisterRequest(email="case@example.com", password="password123", full_name="Case")
    await register_user(db, request)
    user = await get_user_by_email(db, "CASE@EXAMPLE.COM")
    assert user is not None


async def test_get_user_by_email_returns_none_when_missing(db: AsyncSession):
    user = await get_user_by_email(db, "nobody@example.com")
    assert user is None


async def test_authenticate_user_success(db: AsyncSession):
    request = RegisterRequest(email="auth@example.com", password="correctpass", full_name="Auth")
    await register_user(db, request)
    user = await authenticate_user(db, "auth@example.com", "correctpass")
    assert user is not None
    assert user.email == "auth@example.com"


async def test_authenticate_user_wrong_password(db: AsyncSession):
    request = RegisterRequest(
        email="authwrong@example.com", password="correctpass", full_name="Auth"
    )
    await register_user(db, request)
    user = await authenticate_user(db, "authwrong@example.com", "wrongpass")
    assert user is None


async def test_authenticate_user_nonexistent_email(db: AsyncSession):
    user = await authenticate_user(db, "ghost@example.com", "password")
    assert user is None


async def test_authenticate_inactive_user_returns_none(db: AsyncSession):
    request = RegisterRequest(
        email="inactive@example.com", password="password123", full_name="Inactive"
    )
    created = await register_user(db, request)
    created.is_active = False
    await db.commit()

    user = await authenticate_user(db, "inactive@example.com", "password123")
    assert user is None
