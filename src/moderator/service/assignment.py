import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from moderator.exception import ModeratorWorkerAssignmentNotFoundException
from moderator.model import ModeratorWorker, ModeratorWorkerAssignment
from moderator.schema import ModeratorWorkerAssignmentResponse
from moderator.service.moderator import ModeratorService
from moderator.service.worker import ModeratorWorkerService


class ModeratorWorkerAssignmentService:

    def __init__(self, moderator_worker_service: ModeratorWorkerService, moderator_service: ModeratorService):
        self._moderator_service = moderator_service
        self._moderator_worker_service = moderator_worker_service

    async def assign(
        self,
        moderator_id: uuid.UUID,
        worker_id: str,
        db_sess: AsyncSession,
    ) -> ModeratorWorkerAssignmentResponse:
        mod = await self._moderator_service.get_by_id(moderator_id, db_sess)

        assignment = await db_sess.scalar(
            select(ModeratorWorkerAssignment).where(
                ModeratorWorkerAssignment.moderator_id == moderator_id
            )
        )
        if assignment is None:
            assignment = ModeratorWorkerAssignment(
                moderator_id=moderator_id,
                worker_id=worker_id,
            )
            db_sess.add(assignment)
            await self._moderator_worker_service.increment_count(worker_id, db_sess)
        elif assignment.worker_id != worker_id:
            await self._moderator_worker_service.decrement_count(
                assignment.worker_id, db_sess
            )
            assignment.worker_id = worker_id
            await self._moderator_worker_service.increment_count(worker_id, db_sess)

        await db_sess.flush()
        await db_sess.refresh(assignment)
        return ModeratorWorkerAssignmentResponse.from_model(assignment)

    async def release(self, moderator_id: uuid.UUID, db_sess: AsyncSession) -> None:
        assignment = await db_sess.scalar(
            select(ModeratorWorkerAssignment).where(
                ModeratorWorkerAssignment.moderator_id == moderator_id
            )
        )
        if assignment is None:
            raise ModeratorWorkerAssignmentNotFoundException()

        worker = await db_sess.scalar(
            select(ModeratorWorker)
            .where(ModeratorWorker.id == assignment.worker_id)
            .with_for_update()
        )
        if worker is not None:
            worker.count = max(worker.count - 1, 0)

        await db_sess.delete(assignment)

    async def get_by_moderator(
        self, moderator_id: uuid.UUID, db_sess: AsyncSession
    ) -> ModeratorWorkerAssignmentResponse:
        assignment = await db_sess.scalar(
            select(ModeratorWorkerAssignment).where(
                ModeratorWorkerAssignment.moderator_id == moderator_id
            )
        )
        if assignment is None:
            raise ModeratorWorkerAssignmentNotFoundException()
        return ModeratorWorkerAssignmentResponse.from_model(assignment)

    async def list_by_worker(
        self, worker_id: str, db_sess: AsyncSession
    ) -> list[ModeratorWorkerAssignmentResponse]:
        result = await db_sess.execute(
            select(ModeratorWorkerAssignment).where(
                ModeratorWorkerAssignment.worker_id == worker_id
            )
        )
        return [
            ModeratorWorkerAssignmentResponse.from_model(assignment)
            for assignment in result.scalars().all()
        ]
