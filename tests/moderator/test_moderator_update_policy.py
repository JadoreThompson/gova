import uuid
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from config import KAFKA_MODERATOR_EVENTS_TOPIC
from core.db.session import get_db_session
from event.publisher import EventPublisher
from moderator.event import ModeratorEventType, ModeratorPolicyUpdatedEvent
from moderator.exception import ModeratorNotFoundException
from moderator.model import Moderator
from moderator.schema import ModeratorPolicyUpdate
from moderator.service.moderator import ModeratorService
from .util import make_create


def make_service():
    publisher = AsyncMock(spec=EventPublisher)
    return ModeratorService(publisher), publisher


@pytest.mark.asyncio(loop_scope="session")
async def test_update_policy_changes_policy_and_publishes_event(create_user):
    user_id = create_user()
    service, publisher = make_service()

    async with get_db_session() as db_sess:
        moderator = await service.create(
            make_create(community_policy="Old policy."), user_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await service.update_policy(
            moderator.id,
            user_id,
            ModeratorPolicyUpdate(community_policy="New policy."),
            db_sess,
        )
        await db_sess.commit()

    assert result.id == moderator.id
    assert result.community_policy == "New policy."

    async with get_db_session() as db_sess:
        stored = await db_sess.get(Moderator, moderator.id)

    assert stored.community_policy == "New policy."

    event, topic, published_db_sess = publisher.publish.await_args.args
    assert isinstance(event, ModeratorPolicyUpdatedEvent)
    assert event.moderator_id == moderator.id
    assert event.type == ModeratorEventType.POLICY_UPDATED
    assert "community_policy" not in event.model_dump()
    assert set(event.model_dump()) == {"moderator_id", "timestamp", "type"}
    assert topic == KAFKA_MODERATOR_EVENTS_TOPIC


@pytest.mark.asyncio(loop_scope="session")
async def test_update_policy_does_not_publish_for_unowned_moderator(create_user):
    owner_id = create_user()
    other_id = create_user()
    service, publisher = make_service()

    async with get_db_session() as db_sess:
        moderator = await service.create(make_create(), owner_id, db_sess)
        await db_sess.commit()

    with pytest.raises(ModeratorNotFoundException):
        async with get_db_session() as db_sess:
            await service.update_policy(
                moderator.id,
                other_id,
                ModeratorPolicyUpdate(community_policy="Hacked policy."),
                db_sess,
            )

    publisher.publish.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="session")
async def test_update_policy_raises_when_moderator_missing(create_user):
    service, publisher = make_service()

    with pytest.raises(ModeratorNotFoundException):
        async with get_db_session() as db_sess:
            await service.update_policy(
                uuid.uuid4(),
                create_user(),
                ModeratorPolicyUpdate(community_policy="Any policy."),
                db_sess,
            )

    publisher.publish.assert_not_awaited()


def test_update_policy_rejects_blank_policy():
    with pytest.raises(ValidationError):
        ModeratorPolicyUpdate(community_policy="   ")
