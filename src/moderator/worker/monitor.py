import asyncio
import logging

import aiohttp
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from moderator.enums import ModeratorPlatform
from core.db.session import get_db_session
from lib.util import get_datetime
from moderator.enums import ModeratorStatus, ModeratorWorkerStatus
from moderator.model import ModeratorWorker, Moderator
from moderator.service.assignment import ModeratorWorkerAssignmentService
from moderator.service.worker import ModeratorWorkerService


class ModeratorWorkerMonitor:
    """
    Periodically inspect the moderator workers table. If a worker's
    heartbeat has timed out, send a /ping request. if this fails, reassign
    the moderator instances onto available nodes
    """

    def __init__(
        self,
        moderator_worker_service: ModeratorWorkerService,
        moderator_worker_assignment_service: ModeratorWorkerAssignmentService,
        heartbeat_timeout: int = 10,
        last_attempt_timeout: int = 10,
        interval: int = 5,
        request_timeout: float = 5.0,
        concurrency: int = 20,
    ) -> None:
        self._moderator_worker_service = moderator_worker_service
        self._moderator_worker_assignment_service = moderator_worker_assignment_service
        self._heartbeat_timeout = heartbeat_timeout
        self._last_attempt_timeout = last_attempt_timeout
        self._interval = interval
        self._request_timeout = request_timeout
        self._concurrency = concurrency
        self._logger = logging.getLogger(self.__class__.__name__)

    async def run(self):
        while True:
            try:
                await self.poll()
            except Exception:
                self._logger.exception("Moderator worker monitor poll failed")
            await asyncio.sleep(self._interval)

    async def poll(self):
        now = self._now()
        workers = await self._claim_stale_workers(now)
        self._logger.info("Found %s stale workers", len(workers))
        if not workers:
            return

        results = await self._ping_all(workers)
        for worker, alive in zip(workers, results):
            if alive:
                self._logger.info("Worker %s is alive, skipping migration", worker[0])
                continue

            self._logger.info("Worker %s is dead, initiating migration", worker[0])
            try:
                await self._handle_failed_worker(worker)
            except Exception:
                self._logger.exception(
                    "Failed to migrate moderators off worker '%s'", worker[0]
                )

    async def _claim_stale_workers(
        self, now: int
    ) -> list[tuple[str, str, int, ModeratorPlatform]]:
        async with get_db_session() as db_sess:
            result = await db_sess.scalars(
                sa.select(ModeratorWorker)
                .where(
                    ModeratorWorker.last_heartbeat <= now - self._heartbeat_timeout,
                    sa.func.coalesce(ModeratorWorker.last_attempt, 0)
                    <= now - self._last_attempt_timeout,
                )
                .with_for_update(skip_locked=True)
            )
            workers = list(result.all())

            for worker in workers:
                worker.last_attempt = now

            return [
                (w.id, w.host, w.port, ModeratorPlatform(w.platform)) for w in workers
            ]

    async def _ping_all(
        self, workers: list[tuple[str, str, int, ModeratorPlatform]]
    ) -> list[bool]:
        semaphore = asyncio.Semaphore(self._concurrency)

        async def ping(host: str, port: int) -> bool:
            async with semaphore:
                return await self._ping(host, port)

        return list(await asyncio.gather(*(ping(w[1], w[2]) for w in workers)))

    async def _ping(self, host: str, port: int) -> bool:
        timeout = aiohttp.ClientTimeout(total=self._request_timeout)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"http://{host}:{port}/ping") as response:
                    return response.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def _handle_failed_worker(
        self, worker: tuple[str, str, int, ModeratorPlatform]
    ) -> None:
        worker_id, _, _, platform = worker

        async with get_db_session() as db_sess:
            stored = await db_sess.get(ModeratorWorker, worker_id, with_for_update=True)
            if stored is None:
                return

            stored.status = ModeratorWorkerStatus.OFFLINE
            stored.count = 0
            await db_sess.flush()

            assignments = (
                await self._moderator_worker_assignment_service.list_by_worker(
                    worker_id, db_sess
                )
            )
            for assignment in assignments:
                await db_sess.execute(
                    sa.update(Moderator)
                    .where(Moderator.id == assignment.moderator_id)
                    .values(status=ModeratorStatus.UNAVAILABLE.value)
                )

                target = await self._find_available_worker(platform, worker_id, db_sess)
                if target is None:
                    await self._moderator_worker_assignment_service.release(
                        assignment.moderator_id, db_sess
                    )
                    await db_sess.execute(
                        sa.update(Moderator)
                        .where(Moderator.id == assignment.moderator_id)
                        .values(status=ModeratorStatus.OFFLINE.value)
                    )
                    continue

                await self._moderator_worker_assignment_service.assign(
                    assignment.moderator_id,
                    target.id,
                    db_sess,
                )

    async def _find_available_worker(
        self,
        platform: ModeratorPlatform,
        exclude_worker_id: str,
        db_sess: AsyncSession,
    ) -> ModeratorWorker | None:
        return await db_sess.scalar(
            sa.select(ModeratorWorker)
            .where(
                ModeratorWorker.id != exclude_worker_id,
                ModeratorWorker.count < ModeratorWorker.capacity,
                ModeratorWorker.status == ModeratorWorkerStatus.ONLINE.value,
                ModeratorWorker.platform == platform,
            )
            .order_by(
                (ModeratorWorker.capacity - ModeratorWorker.count).desc(),
                ModeratorWorker.last_heartbeat.desc(),
            )
            .limit(1)
            .with_for_update()
        )

    @staticmethod
    def _now() -> int:
        return int(get_datetime().timestamp())
