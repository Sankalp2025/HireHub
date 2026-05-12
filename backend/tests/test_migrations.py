from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from tests.conftest import BACKEND_DIR, test_engine


def test_alembic_has_single_head():
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)

    heads = script.get_heads()

    assert len(heads) == 1


async def test_test_database_is_at_alembic_head():
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()

    async with test_engine.connect() as connection:
        current = await connection.run_sync(
            lambda sync_connection: MigrationContext.configure(sync_connection)
            .get_current_revision()
        )

    assert current == head
