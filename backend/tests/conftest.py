import asyncio
import os
import re
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DEFAULT_DB_HOST = "db" if Path("/.dockerenv").exists() else "localhost"
DEFAULT_TEST_DATABASE_URL = (
    f"postgresql+asyncpg://hirehub:hirehub_dev@{DEFAULT_DB_HOST}:5432/hirehub_test"
)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    DEFAULT_TEST_DATABASE_URL,
)
if "_test" not in TEST_DATABASE_URL:
    raise RuntimeError(
        "Refusing to run tests against a database URL that does not look like a "
        "dedicated test database. Set TEST_DATABASE_URL to a database containing '_test'."
    )

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault("BACKEND_CORS_ORIGINS", '["http://localhost:5173"]')

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from tests.factories import user_payload  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _validate_test_database_name(database_name: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise RuntimeError("Test database name may only contain letters, numbers, and underscores.")
    if "_test" not in database_name:
        raise RuntimeError("Test database name must contain '_test'.")


async def _ensure_test_database_exists() -> None:
    url = make_url(TEST_DATABASE_URL)
    database_name = url.database
    if database_name is None:
        raise RuntimeError("TEST_DATABASE_URL must include a database name.")
    _validate_test_database_name(database_name)

    admin_url = url.set(database="postgres")
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
            {"database_name": database_name},
        )
        if exists is None:
            await conn.execute(text(f'CREATE DATABASE "{database_name}"'))
    await admin_engine.dispose()


asyncio.run(_ensure_test_database_exists())

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

TABLES_IN_FK_ORDER = [
    "analysis_results",
    "job_descriptions",
    "resumes",
    "refresh_tokens",
    "users",
]


async def _truncate_test_tables() -> None:
    async with test_engine.connect() as conn:
        table_names = ", ".join(TABLES_IN_FK_ORDER)
        await conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
        await conn.commit()


@pytest.fixture(scope="session", autouse=True)
def _run_migrations():
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(cfg, "head")


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
async def _truncate_tables(request: pytest.FixtureRequest):
    if "client" not in request.fixturenames and "db" not in request.fixturenames:
        yield
        return

    await _truncate_test_tables()
    yield
    await _truncate_test_tables()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def register_user(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "testpassword123",
    full_name: str = "Test User",
) -> dict:
    resp = await client.post(
        "/api/v1/auth/register",
        json=user_payload(email=email, password=password, full_name=full_name),
    )
    assert resp.status_code == 201
    return resp.json()["data"]


async def login_user(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "testpassword123",
) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    return resp.json()["data"]


async def auth_headers_for(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "testpassword123",
    full_name: str = "Test User",
) -> dict[str, str]:
    await register_user(client, email=email, password=password, full_name=full_name)
    tokens = await login_user(client, email=email, password=password)
    return {"Authorization": f"Bearer {tokens['access_token']}"}
