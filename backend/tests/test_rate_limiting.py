import pytest
from httpx import AsyncClient

from app.limiter import limiter
from tests.conftest import register_user


@pytest.fixture
def rate_limit_on():
    """Enable rate limiting for the duration of the test, then restore it."""
    limiter.reset()
    limiter.enabled = True
    yield
    limiter.enabled = False
    limiter.reset()


async def test_login_rate_limit_enforced(client: AsyncClient, rate_limit_on):
    await register_user(client)
    for _ in range(10):
        await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert resp.status_code == 429
    body = resp.json()
    assert body["data"] is None
    assert body["error"]["code"] == "rate_limit_exceeded"


async def test_register_rate_limit_enforced(client: AsyncClient, rate_limit_on):
    for i in range(10):
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"user{i}@example.com",
                "password": "testpassword123",
                "full_name": f"User {i}",
            },
        )
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "overflow@example.com",
            "password": "testpassword123",
            "full_name": "Overflow",
        },
    )
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "rate_limit_exceeded"


async def test_rate_limit_response_has_error_envelope(client: AsyncClient, rate_limit_on):
    """The 429 response must use the standard API error envelope, not raw slowapi output."""
    await register_user(client)
    for _ in range(10):
        await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert resp.status_code == 429
    body = resp.json()
    assert "data" in body
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
