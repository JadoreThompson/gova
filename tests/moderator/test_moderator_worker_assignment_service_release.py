import uuid

import pytest

from core.db.session import get_db_session
from moderator.exception import ModeratorWorkerAssignmentNotFoundException
from moderator.model import ModeratorWorker
from moderator.schema import ModeratorWorkerCreate
from .util import make_moderator


@pytest.mark.asyncio(loop_scope="session")
async def test_release_decrements_worker_count_and_removes_assignment(
    moderator_service,
    community_service,
    create_user,
    moderator_worker_service,
    moderator_worker_assignment_service,
):
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

    moderator = await make_moderator(
        moderator_service, community_service, create_user()
    )
    moderator_id = moderator.id
    async with get_db_session() as db_sess:
        await moderator_worker_assignment_service.assign(
            moderator_id, worker.id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        stored = await db_sess.get(ModeratorWorker, worker.id)
        stored.count = 1
        await db_sess.commit()

    async with get_db_session() as db_sess:
        assigned = await moderator_worker_service.get_by_id(worker.id, db_sess)
        assert assigned.count == 1

    async with get_db_session() as db_sess:
        await moderator_worker_assignment_service.release(moderator_id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        released = await moderator_worker_service.get_by_id(worker.id, db_sess)
        assert released.count == 0
        with pytest.raises(ModeratorWorkerAssignmentNotFoundException):
            await moderator_worker_assignment_service.get_by_moderator(
                moderator_id, db_sess
            )


@pytest.mark.asyncio(loop_scope="session")
async def test_release_raises_for_unassigned_moderator(
    moderator_worker_assignment_service,
):
    async with get_db_session() as db_sess:
        with pytest.raises(ModeratorWorkerAssignmentNotFoundException):
            await moderator_worker_assignment_service.release(uuid.uuid4(), db_sess)
