import pytest

from core.db.session import get_db_session
from .util import make_community, make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_only_users_moderators(
    moderator_service, community_service, create_user
):
    user_id = create_user()
    other_id = create_user()
    community = await make_community(community_service, user_id)
    other_community = await make_community(community_service, other_id)

    async with get_db_session() as db_sess:
        own = await moderator_service.create(
            make_create(community.id, name="Own"), user_id, db_sess
        )
        await moderator_service.create(
            make_create(other_community.id, name="Other"), other_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        moderators, has_next = await moderator_service.list(user_id, db_sess)

    assert [moderator.id for moderator in moderators] == [own.id]
    assert has_next is False


@pytest.mark.asyncio(loop_scope="session")
async def test_list_filters_by_community(
    moderator_service, community_service, create_user
):
    user_id = create_user()
    first_community = await make_community(community_service, user_id)
    second_community = await make_community(community_service, user_id)

    async with get_db_session() as db_sess:
        first = await moderator_service.create(
            make_create(first_community.id), user_id, db_sess
        )
        await moderator_service.create(
            make_create(second_community.id), user_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        moderators, _ = await moderator_service.list(
            user_id, db_sess, community_id=first_community.id
        )

    assert [moderator.id for moderator in moderators] == [first.id]
