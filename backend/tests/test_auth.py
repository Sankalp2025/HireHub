from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.security import hash_refresh_token
from tests.conftest import TestSessionLocal, auth_headers_for, login_user, register_user


async def test_register_returns_201_without_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "securepass1",
            "full_name": "New User",
        },
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert "password" not in data
    assert "hashed_password" not in data


async def test_register_duplicate_returns_400_generic(client: AsyncClient):
    await register_user(client, email="dup@example.com")
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "password": "securepass1",
            "full_name": "Dup User",
        },
    )
    assert resp.status_code == 400
    assert "already" not in resp.json()["error"]["message"].lower()


async def test_login_success(client: AsyncClient):
    await register_user(client)
    tokens = await login_user(client)
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] > 0


async def test_login_wrong_password(client: AsyncClient):
    await register_user(client)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


async def test_me_with_token(client: AsyncClient):
    headers = await auth_headers_for(client)
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["email"] == "test@example.com"


async def test_me_without_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_swagger_token_endpoint(client: AsyncClient):
    await register_user(client)
    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_refresh_rotation(client: AsyncClient):
    await register_user(client)
    tokens = await login_user(client)
    old_refresh = tokens["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert resp.status_code == 200
    new_tokens = resp.json()["data"]
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]
    assert new_tokens["refresh_token"] != old_refresh


async def test_new_refresh_token_works_after_rotation(client: AsyncClient):
    await register_user(client)
    tokens = await login_user(client)

    rotate_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert rotate_resp.status_code == 200
    rotated_refresh = rotate_resp.json()["data"]["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated_refresh},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["refresh_token"] != rotated_refresh


async def test_old_refresh_token_rejected_after_rotation(client: AsyncClient):
    await register_user(client)
    tokens = await login_user(client)
    old_refresh = tokens["refresh_token"]

    await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert resp.status_code == 401


async def test_invalid_refresh_token_rejected_generically(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not-a-real-refresh-token"},
    )
    assert resp.status_code == 401
    assert "refresh token" in resp.json()["error"]["message"].lower()


async def test_expired_refresh_token_rejected(client: AsyncClient):
    await register_user(client)
    tokens = await login_user(client)
    refresh = tokens["refresh_token"]

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_refresh_token(refresh)
            )
        )
        token = result.scalar_one()
        token.expires_at = datetime.now(UTC) - timedelta(days=1)
        await session.commit()

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert resp.status_code == 401


async def test_inactive_user_refresh_token_rejected(client: AsyncClient):
    await register_user(client)
    tokens = await login_user(client)
    refresh = tokens["refresh_token"]

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one()
        user.is_active = False
        await session.commit()

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert resp.status_code == 401


async def test_logout(client: AsyncClient):
    await register_user(client)
    tokens = await login_user(client)

    resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert resp.status_code == 204


async def test_refresh_after_logout_fails(client: AsyncClient):
    await register_user(client)
    tokens = await login_user(client)
    refresh = tokens["refresh_token"]

    await client.post("/api/v1/auth/logout", json={"refresh_token": refresh})

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert resp.status_code == 401
