import uuid

import pytest
import sqlalchemy as sa

from moderator.enums import ModeratorPlatform
from core.db.session import get_db_session
from lib.util import get_datetime
from moderator.enums import ModeratorStatus, ModeratorWorkerStatus
from moderator.model import ModeratorWorker, ModeratorWorkerAssignment, Moderator
from moderator.worker.monitor import ModeratorWorkerMonitor
from .util import make_moderator


def make_monitor(
    moderator_worker_service, moderator_worker_assignment_service, monkeypatch, *, alive
):
    monitor = ModeratorWorkerMonitor(
        moderator_worker_service=moderator_worker_service,
        moderator_worker_assignment_service=moderator_worker_assignment_service,
        heartbeat_timeout=1,
        last_attempt_timeout=1,
        interval=1,
        request_timeout=0.1,
        concurrency=4,
    )

    async def ping(host: str, port: int) -> bool:
        return alive

    monkeypatch.setattr(monitor, "_ping", ping)
    return monitor


async def register_worker(
    service, *, platform: ModeratorPlatform = ModeratorPlatform.DISCORD, capacity: int
):
    from moderator.schema import ModeratorWorkerCreate

    async with get_db_session() as db_sess:
        worker = await service.register(
            ModeratorWorkerCreate(
                id=f"worker-{uuid.uuid4().hex}",
                host=f"worker-{uuid.uuid4().hex}",
                port=9000,
                capacity=capacity,
                platform=platform,
            ),
            db_sess,
        )
        await db_sess.commit()
        return worker


async def assign_directly(moderator_id, worker_id):
    async with get_db_session() as db_sess:
        db_sess.add(
            ModeratorWorkerAssignment(
                moderator_id=moderator_id,
                worker_id=worker_id,
            )
        )
        await db_sess.commit()


async def make_stale(worker_id, *, last_heartbeat: int = 0, last_attempt: int = 0):
    async with get_db_session() as db_sess:
        worker = await db_sess.get(ModeratorWorker, worker_id)
        worker.last_heartbeat = last_heartbeat
        worker.last_attempt = last_attempt
        await db_sess.commit()


@pytest.mark.asyncio(loop_scope="session")
async def test_poll_migrates_moderators_off_failed_worker(
    moderator_service,
    create_user,
    moderator_worker_service,
    moderator_worker_assignment_service,
    monkeypatch,
):
    failed = await register_worker(moderator_worker_service, capacity=5)
    available = await register_worker(moderator_worker_service, capacity=1000)
    moderator = await make_moderator(moderator_service, create_user())

    await assign_directly(moderator.id, failed.id)
    await make_stale(failed.id)
    await make_stale(
        available.id,
        last_heartbeat=int(get_datetime().timestamp()),
        last_attempt=0,
    )

    async with get_db_session() as db_sess:
        worker = await db_sess.get(ModeratorWorker, failed.id)
        worker.count = 1
        await db_sess.commit()

    monitor = make_monitor(
        moderator_worker_service,
        moderator_worker_assignment_service,
        monkeypatch,
        alive=False,
    )
    await monitor.poll()

    async with get_db_session() as db_sess:
        failed_worker = await db_sess.get(ModeratorWorker, failed.id)
        assert failed_worker.status == ModeratorWorkerStatus.OFFLINE.value
        assert failed_worker.count == 0

        stored_moderator = await db_sess.get(Moderator, moderator.id)
        assert stored_moderator.status == ModeratorStatus.UNAVAILABLE.value

        assignment = await db_sess.scalar(
            sa.select(ModeratorWorkerAssignment).where(
                ModeratorWorkerAssignment.moderator_id == moderator.id
            )
        )
        assert assignment is not None
        assert assignment.worker_id == available.id


@pytest.mark.asyncio(loop_scope="session")
async def test_poll_sets_moderator_offline_when_no_worker_available(
    moderator_service,
    create_user,
    moderator_worker_service,
    moderator_worker_assignment_service,
    monkeypatch,
):
    failed = await register_worker(
        moderator_worker_service,
        platform=ModeratorPlatform.YOUTUBE,
        capacity=5,
    )
    moderator = await make_moderator(moderator_service, create_user())

    await assign_directly(moderator.id, failed.id)
    await make_stale(failed.id)

    async with get_db_session() as db_sess:
        worker = await db_sess.get(ModeratorWorker, failed.id)
        worker.count = 1
        await db_sess.commit()

    monitor = make_monitor(
        moderator_worker_service,
        moderator_worker_assignment_service,
        monkeypatch,
        alive=False,
    )
    await monitor.poll()

    async with get_db_session() as db_sess:
        stored_moderator = await db_sess.get(Moderator, moderator.id)
        assert stored_moderator.status == ModeratorStatus.OFFLINE.value

        assignment = await db_sess.scalar(
            sa.select(ModeratorWorkerAssignment).where(
                ModeratorWorkerAssignment.moderator_id == moderator.id
            )
        )
        assert assignment is None


@pytest.mark.asyncio(loop_scope="session")
async def test_poll_keeps_worker_when_ping_succeeds(
    moderator_worker_service,
    moderator_worker_assignment_service,
    monkeypatch,
):
    worker = await register_worker(moderator_worker_service, capacity=5)
    await make_stale(worker.id)

    monitor = make_monitor(
        moderator_worker_service,
        moderator_worker_assignment_service,
        monkeypatch,
        alive=True,
    )
    await monitor.poll()

    async with get_db_session() as db_sess:
        stored = await db_sess.get(ModeratorWorker, worker.id)
        assert stored.status == ModeratorWorkerStatus.ONLINE.value
        assert stored.last_attempt >= int(get_datetime().timestamp()) - 5
