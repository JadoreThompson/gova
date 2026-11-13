import json
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from moderator.event import (
    ModeratorPingEvent,
    ModeratorStartEvent,
    ModeratorStopEvent,
)
from tests.moderator.util import create_manager


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    ("event_type", "handler_name"),
    [
        ("start", "start_moderator"),
        ("stop", "stop_moderator"),
        ("ping", "ping_moderator"),
    ],
)
async def test_start_dispatches_moderator_events(event_type, handler_name):
    moderator_id = uuid.uuid4()
    message = SimpleNamespace(
        value=json.dumps({"type": event_type, "moderator_id": str(moderator_id)})
    )

    class Consumer:
        def __aiter__(self):
            async def messages():
                yield message

            return messages()

    manager, *_ = create_manager(consumer=Consumer())
    handler = AsyncMock()
    setattr(manager, handler_name, handler)

    await manager.start()

    handler.assert_awaited_once()
    event = handler.await_args.args[0]
    expected_types = {
        "start": ModeratorStartEvent,
        "stop": ModeratorStopEvent,
        "ping": ModeratorPingEvent,
    }
    assert isinstance(event, expected_types[event_type])
    assert event.moderator_id == moderator_id
