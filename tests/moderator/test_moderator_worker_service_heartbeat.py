import uuid

import pytest

from core.db.session import get_db_session
from moderator.exception import ModeratorWorkerNotFoundException
from moderator.schema import ModeratorWorkerCreate


@pytest.mark.asyncio(loop_scope="session")
async def test_heartbeat_updates_last_heartbeat(moderator_worker_service):
    async with get_db_session() as db_sess:
        worker = await moderator_worker_service.register(
            ModeratorWorkerCreate(
                id=f"worker-{uuid.uuid4().hex}",
                host=f"worker-{uuid.uuid4().hex}",
                port=9000,
                capacity=5,
            ),
            db_sess,
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        updated = await moderator_worker_service.heartbeat(worker.id, db_sess)
        await db_sess.commit()

    assert updated.id == worker.id
    assert updated.last_heartbeat >= worker.last_heartbeat


@pytest.mark.asyncio(loop_scope="session")
async def test_heartbeat_raises_for_unknown_worker(moderator_worker_service):
    async with get_db_session() as db_sess:
        with pytest.raises(ModeratorWorkerNotFoundException):
            await moderator_worker_service.heartbeat(str(uuid.uuid4()), db_sess)
