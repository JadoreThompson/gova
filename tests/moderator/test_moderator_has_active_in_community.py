import pytest

from core.db.session import get_db_session
from moderator.enums import ModeratorStatus
from .util import make_community, make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_has_active_in_community_returns_true_for_online_moderator(
    moderator_service, community_service, create_user
):
    user_id = create_user()
    community = await make_community(community_service, user_id)

    async with get_db_session() as db_sess:
        moderator = await moderator_service.create(
            make_create(community.id), user_id, db_sess
        )
        moderator.status = ModeratorStatus.ONLINE
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await moderator_service.has_active_in_community(community.id, db_sess)

    assert result is True


@pytest.mark.asyncio(loop_scope="session")
async def test_has_active_in_community_returns_false_for_offline_moderator(
    moderator_service, community_service, create_user
):
    user_id = create_user()
    community = await make_community(community_service, user_id)

    async with get_db_session() as db_sess:
        await moderator_service.create(make_create(community.id), user_id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await moderator_service.has_active_in_community(community.id, db_sess)

    assert result is False


@pytest.mark.asyncio(loop_scope="session")
async def test_has_active_in_community_returns_false_when_no_moderators(
    moderator_service, community_service, create_user
):
    user_id = create_user()
    community = await make_community(community_service, user_id)

    async with get_db_session() as db_sess:
        result = await moderator_service.has_active_in_community(community.id, db_sess)

    assert result is False
