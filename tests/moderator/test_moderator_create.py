import pytest

from core.db.session import get_db_session
from moderator.enums import ModeratorStatus
from moderator.model import Moderators
from moderator.schema import ModeratorCreate, ModeratorResponse
from .util import make_community, make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_create_links_moderator_to_user_and_community(
    moderator_service, community_service, create_user
):
    user_id = create_user()
    community = await make_community(community_service, user_id)

    async with get_db_session() as db_sess:
        moderator = await moderator_service.create(
            make_create(community.id), user_id, db_sess
        )
        await db_sess.commit()

    assert isinstance(moderator, ModeratorResponse)
    assert moderator.community_id == community.id
    assert moderator.name == "Moderator"
    assert moderator.status == ModeratorStatus.OFFLINE

    async with get_db_session() as db_sess:
        stored = await db_sess.get(Moderators, moderator.id)

    assert stored is not None
    assert stored.user_id == user_id


def test_create_payload_does_not_accept_user_id():
    assert "user_id" not in ModeratorCreate.model_fields


def test_response_does_not_expose_user_id():
    assert "user_id" not in ModeratorResponse.model_fields
