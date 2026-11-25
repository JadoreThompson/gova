import pytest

from core.db.session import get_db_session
from moderator.enums import ModeratorPlatform
from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_only_users_moderators(moderator_service, create_user):
    user_id = create_user()
    other_id = create_user()

    async with get_db_session() as db_sess:
        own = await moderator_service.create(
            make_create(name="Own"), user_id, db_sess
        )
        await moderator_service.create(
            make_create(name="Other"), other_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        moderators, has_next = await moderator_service.list(user_id, db_sess)

    assert [moderator.id for moderator in moderators] == [own.id]
    assert has_next is False


@pytest.mark.asyncio(loop_scope="session")
async def test_list_filters_by_community(moderator_service, create_user):
    user_id = create_user()
    first_request = make_create()
    second_request = make_create()

    async with get_db_session() as db_sess:
        first = await moderator_service.create(first_request, user_id, db_sess)
        await moderator_service.create(second_request, user_id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        moderators, _ = await moderator_service.list(
            user_id,
            db_sess,
            platform=first_request.platform,
            platform_community_id=first_request.platform_community_id,
        )

    assert [moderator.id for moderator in moderators] == [first.id]


@pytest.mark.asyncio(loop_scope="session")
async def test_list_filters_by_platform(moderator_service, create_user):
    user_id = create_user()
    community_id = "shared-community"

    async with get_db_session() as db_sess:
        discord = await moderator_service.create(
            make_create(
                platform=ModeratorPlatform.DISCORD,
                platform_community_id=community_id,
            ),
            user_id,
            db_sess,
        )
        await moderator_service.create(
            make_create(
                platform=ModeratorPlatform.TWITCH,
                platform_community_id=community_id,
            ),
            user_id,
            db_sess,
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        moderators, _ = await moderator_service.list(
            user_id, db_sess, platform=ModeratorPlatform.DISCORD
        )

    assert [moderator.id for moderator in moderators] == [discord.id]
