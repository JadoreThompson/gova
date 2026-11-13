import uuid
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from config import KAFKA_MODERATOR_EVENTS_TOPIC
from moderator.event import ModeratorPingEvent
from moderator.registry import ModeratorRegistry
from tests.moderator.util import create_manager


@pytest.mark.asyncio(loop_scope="session")
async def test_ping_moderator_publishes_ping_for_registered_moderator(monkeypatch):
    moderator_id = uuid.uuid4()
    db_sess = object()

    @asynccontextmanager
    async def db_session():
        yield db_sess

    monkeypatch.setattr("moderator.manager.get_db_session", db_session)
    registry = ModeratorRegistry()
    registry.add_moderator(SimpleNamespace(id=moderator_id))
    manager, _, _, publisher = create_manager(registry=registry)

    await manager.ping_moderator(ModeratorPingEvent(moderator_id=moderator_id))

    published_event, topic, published_db_sess = publisher.publish.await_args.args
    assert isinstance(published_event, ModeratorPingEvent)
    assert published_event.moderator_id == moderator_id
    assert topic == KAFKA_MODERATOR_EVENTS_TOPIC
    assert published_db_sess is db_sess


@pytest.mark.asyncio(loop_scope="session")
async def test_ping_moderator_does_not_publish_for_unregistered_moderator():
    manager, _, _, publisher = create_manager()

    await manager.ping_moderator(ModeratorPingEvent(moderator_id=uuid.uuid4()))

    publisher.publish.assert_not_awaited()
