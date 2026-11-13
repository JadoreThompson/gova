import uuid
from types import SimpleNamespace

import pytest

from config import KAFKA_MODERATOR_EVENTS_TOPIC
from moderator.event import ModeratorPingEvent
from moderator.registry import ModeratorRegistry
from tests.moderator.util import create_manager


@pytest.mark.asyncio(loop_scope="session")
async def test_ping_moderator_publishes_ping_for_registered_moderator():
    moderator_id = uuid.uuid4()
    registry = ModeratorRegistry()
    registry.add_moderator(SimpleNamespace(id=moderator_id))
    manager, _, _, publisher = create_manager(registry=registry)

    await manager.ping_moderator(ModeratorPingEvent(moderator_id=moderator_id))

    published_event, topic = publisher.publish.await_args.args
    assert isinstance(published_event, ModeratorPingEvent)
    assert published_event.moderator_id == moderator_id
    assert topic == KAFKA_MODERATOR_EVENTS_TOPIC


@pytest.mark.asyncio(loop_scope="session")
async def test_ping_moderator_does_not_publish_for_unregistered_moderator():
    manager, _, _, publisher = create_manager()

    await manager.ping_moderator(ModeratorPingEvent(moderator_id=uuid.uuid4()))

    publisher.publish.assert_not_awaited()
