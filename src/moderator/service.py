import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import KAFKA_MODERATOR_EVENTS_TOPIC
from event.publisher import EventPublisher
from moderator.event import (
    ModeratorEvent,
    ModeratorPingEvent,
    ModeratorStartEvent,
    ModeratorStopEvent,
)
from moderator.enums import ModeratorStatus
from moderator.exception import ModeratorNotFoundException
from moderator.model import Moderators
from moderator.schema import ModeratorCreate, ModeratorResponse, ModeratorUpdate


class ModeratorService:
    def __init__(self, event_publisher: EventPublisher):
        self._event_publisher = event_publisher

    async def start(
        self, id: uuid.UUID, user_id: uuid.UUID, db_sess: AsyncSession
    ) -> None:
        await self._publish_control_event(
            ModeratorStartEvent(moderator_id=id), id, user_id, db_sess
        )

    async def stop(
        self, id: uuid.UUID, user_id: uuid.UUID, db_sess: AsyncSession
    ) -> None:
        await self._publish_control_event(
            ModeratorStopEvent(moderator_id=id), id, user_id, db_sess
        )

    async def ping(
        self, id: uuid.UUID, user_id: uuid.UUID, db_sess: AsyncSession
    ) -> None:
        await self._publish_control_event(
            ModeratorPingEvent(moderator_id=id), id, user_id, db_sess
        )

    async def _publish_control_event(
        self,
        event: ModeratorEvent,
        id: uuid.UUID,
        user_id: uuid.UUID,
        db_sess: AsyncSession,
    ) -> None:
        await self.get(id, user_id, db_sess)
        await self._event_publisher.publish(
            event, KAFKA_MODERATOR_EVENTS_TOPIC, db_sess
        )

    async def create(
        self,
        request: ModeratorCreate,
        user_id: uuid.UUID,
        db_sess: AsyncSession,
    ) -> ModeratorResponse:
        moderator = Moderators(
            user_id=user_id,
            community_id=request.community_id,
            name=request.name,
            action_config=request.action_config,
        )
        db_sess.add(moderator)
        await db_sess.flush()
        await db_sess.refresh(moderator)
        return ModeratorResponse.from_model(moderator)

    async def get(
        self, id: uuid.UUID, user_id: uuid.UUID, db_sess: AsyncSession
    ) -> ModeratorResponse:
        moderator = await db_sess.scalar(
            select(Moderators).where(
                Moderators.id == id,
                Moderators.user_id == user_id,
            )
        )
        if moderator is None:
            raise ModeratorNotFoundException()
        return ModeratorResponse.from_model(moderator)

    async def get_by_id(
        self, id: uuid.UUID, db_sess: AsyncSession, lock: bool = True
    ) -> ModeratorResponse:
        moderator = await db_sess.get(Moderators, id, with_for_update=lock)
        if moderator is None:
            raise ModeratorNotFoundException()
        return ModeratorResponse.from_model(moderator)

    async def list(
        self,
        user_id: uuid.UUID,
        db_sess: AsyncSession,
        *,
        community_id: uuid.UUID | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[ModeratorResponse], bool]:
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
        return [
            ModeratorResponse.from_model(moderator) for moderator in moderators[:limit]
        ], has_next

    async def update(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID,
        request: ModeratorUpdate,
        db_sess: AsyncSession,
    ) -> ModeratorResponse:
        moderator = await db_sess.scalar(
            select(Moderators).where(
                Moderators.id == id,
                Moderators.user_id == user_id,
            )
        )
        if moderator is None:
            raise ModeratorNotFoundException()

        if request.name is not None:
            moderator.name = request.name
        if request.action_config is not None:
            moderator.action_config = request.action_config

        await db_sess.flush()
        await db_sess.refresh(moderator)
        return ModeratorResponse.from_model(moderator)

    async def delete(
        self, id: uuid.UUID, user_id: uuid.UUID, db_sess: AsyncSession
    ) -> None:
        moderator = await db_sess.scalar(
            select(Moderators).where(
                Moderators.id == id,
                Moderators.user_id == user_id,
            )
        )
        if moderator is None:
            raise ModeratorNotFoundException()
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
