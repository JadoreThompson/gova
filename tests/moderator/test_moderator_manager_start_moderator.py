import uuid
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from community.enums import CommunityPlatform
from config import KAFKA_MODERATOR_EVENTS_TOPIC
from moderator.enums import ModeratorStatus
from moderator.event import ModeratorStartEvent, ModeratorStartedEvent
from moderator.registry import ModeratorRegistry
from tests.moderator.util import create_manager


@asynccontextmanager
async def db_session(db_sess):
    yield db_sess


@pytest.mark.asyncio(loop_scope="session")
async def test_start_moderator_updates_status_and_publishes_started_event(monkeypatch):
    moderator_id = uuid.uuid4()
    community_id = uuid.uuid4()
    moderator = SimpleNamespace(
        id=moderator_id,
        community_id=community_id,
        status=ModeratorStatus.OFFLINE,
    )
    community = SimpleNamespace(platform=CommunityPlatform.DISCORD)
    registry = ModeratorRegistry()
    manager, moderator_service, community_service, publisher = create_manager(
        registry=registry
    )
    db_sess = SimpleNamespace(execute=AsyncMock(), commit=AsyncMock())
    monkeypatch.setattr(
        "moderator.manager.get_db_session",
        lambda: db_session(db_sess),
    )
    created_moderator = SimpleNamespace(id=moderator_id)
    create_discord = Mock(return_value=created_moderator)
    monkeypatch.setattr(manager, "_create_discord_moderator", create_discord)
    moderator_service.get_by_id.return_value = moderator
    community_service.get_by_id.return_value = community

    await manager.start_moderator(ModeratorStartEvent(moderator_id=moderator_id))

    moderator_service.get_by_id.assert_awaited_once_with(
        moderator_id, db_sess, lock=True
    )
    community_service.get_by_id.assert_awaited_once_with(community_id, db_sess)
    create_discord.assert_called_once_with(community, moderator)
    db_sess.execute.assert_awaited_once()
    db_sess.commit.assert_awaited_once()
    published_event, topic, published_db_sess = publisher.publish.await_args.args
    assert isinstance(published_event, ModeratorStartedEvent)
    assert published_event.moderator_id == moderator_id
    assert topic == KAFKA_MODERATOR_EVENTS_TOPIC
    assert published_db_sess is db_sess


@pytest.mark.asyncio(loop_scope="session")
async def test_start_moderator_skips_a_moderator_already_in_registry():
    moderator_id = uuid.uuid4()
    registry = ModeratorRegistry()
    registry.add_moderator(SimpleNamespace(id=moderator_id))
    manager, moderator_service, *_ = create_manager(registry=registry)

    await manager.start_moderator(ModeratorStartEvent(moderator_id=moderator_id))

    moderator_service.get_by_id.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="session")
async def test_start_moderator_skips_non_offline_moderator():
    moderator_id = uuid.uuid4()
    moderator = SimpleNamespace(status=ModeratorStatus.ONLINE)
    manager, moderator_service, community_service, publisher = create_manager()
    moderator_service.get_by_id.return_value = moderator

    await manager.start_moderator(ModeratorStartEvent(moderator_id=moderator_id))

    community_service.get_by_id.assert_not_awaited()
    publisher.publish.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="session")
async def test_start_moderator_skips_unsupported_platform(monkeypatch):
    moderator_id = uuid.uuid4()
    moderator = SimpleNamespace(
        id=moderator_id,
        community_id=uuid.uuid4(),
        status=ModeratorStatus.OFFLINE,
    )
    community = SimpleNamespace(platform=CommunityPlatform.YOUTUBE)
    manager, moderator_service, community_service, publisher = create_manager()
    db_sess = SimpleNamespace(execute=AsyncMock(), commit=AsyncMock())
    monkeypatch.setattr(
        "moderator.manager.get_db_session",
        lambda: db_session(db_sess),
    )
    moderator_service.get_by_id.return_value = moderator
    community_service.get_by_id.return_value = community

    await manager.start_moderator(ModeratorStartEvent(moderator_id=moderator_id))

    db_sess.execute.assert_not_awaited()
    db_sess.commit.assert_not_awaited()
    publisher.publish.assert_not_awaited()
