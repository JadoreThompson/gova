import uuid

import pytest

from core.db.session import get_db_session
from moderator.model import ModeratorWorker
from moderator.schema import ModeratorWorkerCreate


def make_worker(**overrides) -> ModeratorWorkerCreate:
    values = {
        "id": f"worker-{uuid.uuid4().hex}",
        "host": f"worker-{uuid.uuid4().hex}",
        "port": 9000,
        "capacity": 10,
    }
    values.update(overrides)
    return ModeratorWorkerCreate(**values)


@pytest.mark.asyncio(loop_scope="session")
async def test_register_creates_worker(moderator_worker_service):
    request = make_worker()

    async with get_db_session() as db_sess:
        worker = await moderator_worker_service.register(request, db_sess)
        await db_sess.commit()

    assert worker.host == request.host
    assert worker.port == request.port
    assert worker.capacity == request.capacity
    assert worker.count == 0
    assert worker.last_heartbeat > 0

    async with get_db_session() as db_sess:
        stored = await db_sess.get(ModeratorWorker, worker.id)

    assert stored is not None
    assert stored.host == request.host


@pytest.mark.asyncio(loop_scope="session")
async def test_register_updates_existing_worker(moderator_worker_service):
    request = make_worker(capacity=5)

    async with get_db_session() as db_sess:
        first = await moderator_worker_service.register(request, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        second = await moderator_worker_service.register(
            make_worker(
                id=request.id,
                host=request.host,
                port=request.port,
                capacity=20,
            ),
            db_sess,
        )
        await db_sess.commit()

    assert second.id == first.id
    assert second.capacity == 20
