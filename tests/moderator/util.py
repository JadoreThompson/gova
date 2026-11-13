import uuid
from unittest.mock import AsyncMock

from community.service import CommunityService
from community.enums import CommunityPlatform
from community.schema import CommunityCreate
from core.db.session import get_db_session
from event.publisher import EventPublisher
from moderator.manager import ModeratorManager
from moderator.registry import ModeratorRegistry
from moderator.service import ModeratorService
from moderator.schema import ModeratorCreate


def make_create(community_id: uuid.UUID, **overrides) -> ModeratorCreate:
    values = {
        "community_id": community_id,
        "name": "Moderator",
        "action_config": {},
    }
    values.update(overrides)
    return ModeratorCreate(**values)


async def make_community(community_service, user_id: uuid.UUID):
    async with get_db_session() as db_sess:
        community = await community_service.create(
            CommunityCreate(
                platform=CommunityPlatform.DISCORD,
                community_id=f"community-{uuid.uuid4()}",
                policy="Be nice.",
            ),
            user_id,
            db_sess,
        )
        await db_sess.commit()
        return community


def create_manager(*, consumer=None, registry=None):
    moderator_service = AsyncMock(spec=ModeratorService)
    community_service = AsyncMock(spec=CommunityService)
    event_publisher = AsyncMock(spec=EventPublisher)
    manager = ModeratorManager(
        moderator_service=moderator_service,
        community_service=community_service,
        registry=registry if registry is not None else ModeratorRegistry(),
        kafka_consumer=consumer if consumer is not None else AsyncMock(),
        event_publisher=event_publisher,
    )
    return manager, moderator_service, community_service, event_publisher
