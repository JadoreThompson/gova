import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from config import KAFKA_MODERATOR_EVENTS_TOPIC
from event.publisher import EventPublisher
from moderator.event import (
    ModeratorPingEvent,
    ModeratorStartEvent,
    ModeratorStopEvent,
)
from moderator.exception import ModeratorNotFoundException
from moderator.service import ModeratorService


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    ("method_name", "event_type"),
    [
        ("start", ModeratorStartEvent),
        ("stop", ModeratorStopEvent),
        ("ping", ModeratorPingEvent),
    ],
)
async def test_moderator_control_publishes_owned_moderator_event(
    method_name, event_type
):
    moderator_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db_sess = AsyncMock()
    db_sess.scalar.return_value = SimpleNamespace(
        id=moderator_id,
        community_id=uuid.uuid4(),
        name="Moderator",
        action_config={},
        status="offline",
        created_at=datetime.now(),
    )
    publisher = AsyncMock(spec=EventPublisher)
    service = ModeratorService(publisher)

    await getattr(service, method_name)(moderator_id, user_id, db_sess)

    published_event, topic, published_db_sess = publisher.publish.await_args.args
    assert isinstance(published_event, event_type)
    assert published_event.moderator_id == moderator_id
    assert topic == KAFKA_MODERATOR_EVENTS_TOPIC
    assert published_db_sess is db_sess


@pytest.mark.asyncio(loop_scope="session")
async def test_moderator_control_does_not_publish_for_unowned_moderator():
    db_sess = AsyncMock()
    db_sess.scalar.return_value = None
    publisher = AsyncMock(spec=EventPublisher)
    service = ModeratorService(publisher)

    with pytest.raises(ModeratorNotFoundException):
        await service.start(uuid.uuid4(), uuid.uuid4(), db_sess)

    publisher.publish.assert_not_awaited()
