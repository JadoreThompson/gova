import uuid
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from config import KAFKA_MODERATOR_EVENTS_TOPIC
from moderator.enums import ModeratorStatus
from moderator.event import ModeratorStopEvent, ModeratorStoppedEvent
from moderator.registry import ModeratorRegistry
from tests.moderator.util import create_manager


@asynccontextmanager
async def db_session(db_sess):
    yield db_sess


@pytest.mark.asyncio(loop_scope="session")
async def test_stop_moderator_unregisters_and_publishes_stopped_event(monkeypatch):
    moderator_id = uuid.uuid4()
    moderator = SimpleNamespace(id=moderator_id, status=ModeratorStatus.ONLINE)
    registry = ModeratorRegistry()
    registry.add_moderator(moderator)
    manager, moderator_service, _, publisher = create_manager(registry=registry)
    db_sess = SimpleNamespace(execute=AsyncMock(), commit=AsyncMock())
    monkeypatch.setattr(
        "moderator.manager.get_db_session",
        lambda: db_session(db_sess),
    )
    moderator_service.get_by_id.return_value = moderator

    await manager.stop_moderator(ModeratorStopEvent(moderator_id=moderator_id))

    assert not registry.contains(moderator_id)
    db_sess.execute.assert_awaited_once()
    db_sess.commit.assert_awaited_once()
    published_event, topic, published_db_sess = publisher.publish.await_args.args
    assert isinstance(published_event, ModeratorStoppedEvent)
    assert published_event.moderator_id == moderator_id
    assert topic == KAFKA_MODERATOR_EVENTS_TOPIC
    assert published_db_sess is db_sess


@pytest.mark.asyncio(loop_scope="session")
async def test_stop_moderator_skips_moderator_that_is_not_online(monkeypatch):
    moderator_id = uuid.uuid4()
    moderator = SimpleNamespace(status=ModeratorStatus.OFFLINE)
    manager, moderator_service, _, publisher = create_manager()
    db_sess = SimpleNamespace(execute=AsyncMock(), commit=AsyncMock())
    moderator_service.get_by_id.return_value = moderator
    monkeypatch.setattr(
        "moderator.manager.get_db_session",
        lambda: db_session(db_sess),
    )

    await manager.stop_moderator(ModeratorStopEvent(moderator_id=moderator_id))

    publisher.publish.assert_not_awaited()
    db_sess.execute.assert_not_awaited()
    db_sess.commit.assert_not_awaited()
