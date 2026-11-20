import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from community.enums import CommunityPlatform
from community.service import CommunityService
from config import KAFKA_MODERATOR_EVENTS_TOPIC
from event.publisher import EventPublisher
from moderator.event import ModeratorStartedEvent
from moderator.registry import ModeratorRegistry
from moderator.service.assignment import ModeratorWorkerAssignmentService
from moderator.service.discord import DiscordModeratorService
from moderator.service.manager import ModeratorManagerService
from moderator.service.moderator import ModeratorService


def create_manager():
    moderator_service = AsyncMock(spec=ModeratorService)
    community_service = AsyncMock(spec=CommunityService)
    assignment_service = AsyncMock(spec=ModeratorWorkerAssignmentService)
    event_publisher = AsyncMock(spec=EventPublisher)
    registry = ModeratorRegistry()
    manager = ModeratorManagerService(
        moderator_service=moderator_service,
        community_service=community_service,
        moderator_worker_assignment_service=assignment_service,
        registry=registry,
        event_publisher=event_publisher,
    )
    return (
        manager,
        moderator_service,
        community_service,
        assignment_service,
        registry,
        event_publisher,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_constructs_discord_moderator_and_assigns_worker():
    moderator_id = uuid.uuid4()
    community_id = uuid.uuid4()
    guild_id = int(uuid.uuid4().int % 10**18)
    moderator = SimpleNamespace(id=moderator_id, community_id=community_id)
    community = SimpleNamespace(
        id=community_id,
        platform=CommunityPlatform.DISCORD,
        community_id=str(guild_id),
        policy="Be nice.",
    )
    db_sess = AsyncMock()

    (
        manager,
        moderator_service,
        community_service,
        assignment_service,
        registry,
        event_publisher,
    ) = create_manager()
    moderator_service.get_by_id.return_value = moderator
    community_service.get_by_id.return_value = community

    mod = await manager.create(moderator_id, "worker-1", db_sess)

    moderator_service.get_by_id.assert_awaited_once_with(moderator_id, db_sess)
    community_service.get_by_id.assert_awaited_once_with(community_id, db_sess)
    assert isinstance(mod, DiscordModeratorService)
    assert mod.id == moderator_id
    assert mod.community_id == str(guild_id)
    assert mod.get_policy() == "Be nice."
    assert registry.get(moderator_id) is mod
    assignment_service.assign.assert_awaited_once_with(
        moderator_id, "worker-1", db_sess
    )
    event, topic, published_db_sess = event_publisher.publish.await_args.args
    assert isinstance(event, ModeratorStartedEvent)
    assert event.moderator_id == moderator_id
    assert topic == KAFKA_MODERATOR_EVENTS_TOPIC
    assert published_db_sess is db_sess


@pytest.mark.asyncio(loop_scope="session")
async def test_create_raises_for_unsupported_platform():
    moderator_id = uuid.uuid4()
    moderator = SimpleNamespace(id=moderator_id, community_id=uuid.uuid4())
    community = SimpleNamespace(
        id=moderator.community_id,
        platform=CommunityPlatform.YOUTUBE,
        community_id="youtube-channel",
        policy="Be nice.",
    )

    (
        manager,
        moderator_service,
        community_service,
        assignment_service,
        registry,
        event_publisher,
    ) = create_manager()
    moderator_service.get_by_id.return_value = moderator
    community_service.get_by_id.return_value = community

    with pytest.raises(ValueError):
        await manager.create(moderator_id, "worker-1", AsyncMock())

    assert moderator_id not in registry
    assignment_service.assign.assert_not_awaited()
    event_publisher.publish.assert_not_awaited()
