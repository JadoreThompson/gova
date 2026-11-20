import uuid

import pytest

from core.db.session import get_db_session
from moderator.schema import ModeratorWorkerCreate
from .util import make_moderator


async def register_worker(service, *, capacity: int):
    async with get_db_session() as db_sess:
        worker = await service.register(
            ModeratorWorkerCreate(
                id=f"worker-{uuid.uuid4().hex}",
                host=f"worker-{uuid.uuid4().hex}",
                port=9000,
                capacity=capacity,
            ),
            db_sess,
        )
        await db_sess.commit()
        return worker


@pytest.mark.asyncio(loop_scope="session")
async def test_assign_creates_assignment_record(
    moderator_service,
    community_service,
    create_user,
    moderator_worker_service,
    moderator_worker_assignment_service,
):
    worker = await register_worker(moderator_worker_service, capacity=5)
    moderator = await make_moderator(
        moderator_service, community_service, create_user()
    )

    async with get_db_session() as db_sess:
        assignment = await moderator_worker_assignment_service.assign(
            moderator.id, worker.id, db_sess
        )
        await db_sess.commit()

    assert assignment.moderator_id == moderator.id
    assert assignment.worker_id == worker.id


@pytest.mark.asyncio(loop_scope="session")
async def test_assign_updates_existing_assignment_record(
    moderator_service,
    community_service,
    create_user,
    moderator_worker_service,
    moderator_worker_assignment_service,
):
    first = await register_worker(moderator_worker_service, capacity=5)
    second = await register_worker(moderator_worker_service, capacity=5)
    moderator = await make_moderator(
        moderator_service, community_service, create_user()
    )

    async with get_db_session() as db_sess:
        created = await moderator_worker_assignment_service.assign(
            moderator.id, first.id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        updated = await moderator_worker_assignment_service.assign(
            moderator.id, second.id, db_sess
        )
        await db_sess.commit()

    assert updated.id == created.id
    assert updated.moderator_id == moderator.id
    assert updated.worker_id == second.id
