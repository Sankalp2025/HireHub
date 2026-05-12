import asyncio
import os
import uuid
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from alembic.config import Config


async def create_database(admin_url: str, database_name: str) -> None:
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        await conn.execute(text(f'CREATE DATABASE "{database_name}"'))
    await admin_engine.dispose()


async def drop_database(admin_url: str, database_name: str) -> None:
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        await conn.execute(
            text(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = :db_name
                AND pid <> pg_backend_pid()
                """
            ),
            {"db_name": database_name},
        )
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
    await admin_engine.dispose()


def main() -> None:
    database_url = os.environ.get("TEST_DATABASE_URL") or os.environ["DATABASE_URL"]
    base_url = make_url(database_url)
    temp_db = f"hirehub_migration_test_{uuid.uuid4().hex[:8]}"
    admin_url = base_url.render_as_string(hide_password=False)

    asyncio.run(create_database(admin_url, temp_db))
    try:
        temp_url = base_url.set(database=temp_db).render_as_string(hide_password=False)
        os.environ["DATABASE_URL"] = temp_url
        backend_dir = Path(__file__).resolve().parents[1]
        cfg = Config(str(backend_dir / "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", temp_url)
        command.upgrade(cfg, "head")
    finally:
        asyncio.run(drop_database(admin_url, temp_db))


if __name__ == "__main__":
    main()
