import pytest_asyncio
from sqlalchemy import delete

from core.db.session import get_db_session
from moderator.model import ModeratorWorker, ModeratorWorkerAssignment


@pytest_asyncio.fixture(loop_scope="session", autouse=True)
async def clean_worker_state():
    """Worker queries are global, so isolate them from other tests' rows."""
    async with get_db_session() as db_sess:
        await db_sess.execute(delete(ModeratorWorkerAssignment))
        await db_sess.execute(delete(ModeratorWorker))

    yield

    async with get_db_session() as db_sess:
        await db_sess.execute(delete(ModeratorWorkerAssignment))
        await db_sess.execute(delete(ModeratorWorker))
