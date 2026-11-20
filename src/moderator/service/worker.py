import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from lib.util import get_datetime
from moderator.enums import ModeratorWorkerStatus
from moderator.exception import ModeratorWorkerNotFoundException
from moderator.model import ModeratorWorker, ModeratorWorkerAssignment
from moderator.schema import ModeratorWorkerCreate, ModeratorWorkerResponse


class ModeratorWorkerService:
    async def register(
        self, request: ModeratorWorkerCreate, db_sess: AsyncSession
    ) -> ModeratorWorkerResponse:
        worker = await db_sess.get(ModeratorWorker, request.id)

        now = self._now()
        if worker is None:
            worker = ModeratorWorker(
                id=request.id,
                platform=request.platform,
                host=request.host,
                port=request.port,
                count=0,
                capacity=request.capacity,
                status=ModeratorWorkerStatus.ONLINE,
                last_heartbeat=now,
                last_attempt=0,
            )
            db_sess.add(worker)
        else:
            worker.platform = request.platform
            worker.host = request.host
            worker.port = request.port
            worker.capacity = request.capacity
            worker.status = ModeratorWorkerStatus.ONLINE
            worker.last_heartbeat = now

        await db_sess.flush()
        await db_sess.refresh(worker)
        return ModeratorWorkerResponse.from_model(worker)

    async def heartbeat(
        self, id: str, db_sess: AsyncSession
    ) -> ModeratorWorkerResponse:
        worker = await db_sess.get(ModeratorWorker, id)
        if worker is None:
            raise ModeratorWorkerNotFoundException()

        worker.status = ModeratorWorkerStatus.ONLINE
        worker.last_heartbeat = self._now()
        await db_sess.flush()
        await db_sess.refresh(worker)
        return ModeratorWorkerResponse.from_model(worker)

    async def get_by_id(
        self, id: str, db_sess: AsyncSession
    ) -> ModeratorWorkerResponse:
        worker = await db_sess.get(ModeratorWorker, id)
        if worker is None:
            raise ModeratorWorkerNotFoundException()
        return ModeratorWorkerResponse.from_model(worker)

    async def list(self, db_sess: AsyncSession) -> list[ModeratorWorkerResponse]:
        result = await db_sess.execute(
            sa.select(ModeratorWorker).order_by(
                ModeratorWorker.host, ModeratorWorker.port
            )
        )
        return [
            ModeratorWorkerResponse.from_model(worker)
            for worker in result.scalars().all()
        ]

    async def deregister(self, id: str, db_sess: AsyncSession) -> None:
        worker = await db_sess.get(ModeratorWorker, id)
        if worker is None:
            raise ModeratorWorkerNotFoundException()

        await db_sess.execute(
            sa.delete(ModeratorWorkerAssignment).where(
                ModeratorWorkerAssignment.worker_id == id
            )
        )
        await db_sess.delete(worker)

    async def increment_count(self, id: str, db_sess: AsyncSession) -> None:
        result = await db_sess.execute(
            sa.update(ModeratorWorker)
            .where(ModeratorWorker.id == id)
            .values(count=ModeratorWorker.count + 1)
        )

        if result.rowcount == 0:
            raise ModeratorWorkerNotFoundException()

    async def decrement_count(self, id: str, db_sess: AsyncSession) -> None:
        result = await db_sess.execute(
            sa.update(ModeratorWorker)
            .where(ModeratorWorker.id == id)
            .values(count=sa.func.greatest(ModeratorWorker.count - 1, 0))
        )

        if result.rowcount == 0:
            raise ModeratorWorkerNotFoundException()

    @staticmethod
    def _now() -> int:
        return int(get_datetime().timestamp())
