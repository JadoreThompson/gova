import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from moderator.enums import ModeratorStatus
from moderator.exception import ModeratorNotFoundException
from moderator.model import Moderators
from moderator.schema import ModeratorCreate, ModeratorUpdate


class ModeratorService:
    async def create(
        self,
        request: ModeratorCreate,
        user_id: uuid.UUID,
        db_sess: AsyncSession,
    ) -> Moderators:
        moderator = Moderators(
            user_id=user_id,
            community_id=request.community_id,
            name=request.name,
            action_config=request.action_config,
        )
        db_sess.add(moderator)
        await db_sess.flush()
        await db_sess.refresh(moderator)
        return moderator

    async def get(
        self, id: uuid.UUID, user_id: uuid.UUID, db_sess: AsyncSession
    ) -> Moderators:
        moderator = await db_sess.scalar(
            select(Moderators).where(
                Moderators.id == id,
                Moderators.user_id == user_id,
            )
        )
        if moderator is None:
            raise ModeratorNotFoundException()
        return moderator

    async def list(
        self,
        user_id: uuid.UUID,
        db_sess: AsyncSession,
        *,
        community_id: uuid.UUID | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[Moderators], bool]:
        stmt = (
            select(Moderators)
            .where(Moderators.user_id == user_id)
            .order_by(Moderators.created_at.desc())
        )
        if community_id is not None:
            stmt = stmt.where(Moderators.community_id == community_id)

        result = await db_sess.execute(stmt.offset((page - 1) * limit).limit(limit + 1))
        moderators = list(result.scalars().all())
        has_next = len(moderators) > limit
        return moderators[:limit], has_next

    async def update(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID,
        request: ModeratorUpdate,
        db_sess: AsyncSession,
    ) -> Moderators:
        moderator = await self.get(id, user_id, db_sess)

        if request.name is not None:
            moderator.name = request.name
        if request.action_config is not None:
            moderator.action_config = request.action_config

        await db_sess.flush()
        await db_sess.refresh(moderator)
        return moderator

    async def delete(
        self, id: uuid.UUID, user_id: uuid.UUID, db_sess: AsyncSession
    ) -> None:
        moderator = await self.get(id, user_id, db_sess)
        await db_sess.delete(moderator)

    async def has_active_in_community(
        self, community_id: uuid.UUID, db_sess: AsyncSession
    ) -> bool:
        active_moderator = await db_sess.scalar(
            select(Moderators.id)
            .where(
                Moderators.community_id == community_id,
                Moderators.status != ModeratorStatus.OFFLINE.value,
            )
            .limit(1)
        )
        return active_moderator is not None
