import uuid

import pytest

from core.db.session import get_db_session
from moderator.enums import ModeratorPlatform
from moderator.exception import ModeratorNotFoundException
from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_get_returns_moderator(moderator_service, create_user):
    user_id = create_user()
    request = make_create()

    async with get_db_session() as db_sess:
        moderator = await moderator_service.create(request, user_id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await moderator_service.get(moderator.id, user_id, db_sess)

    assert result.id == moderator.id
    assert result.platform == request.platform
    assert result.platform_community_id == request.platform_community_id
    assert result.community_policy == request.community_policy


@pytest.mark.asyncio(loop_scope="session")
async def test_get_raises_when_moderator_belongs_to_another_user(
    moderator_service, create_user
):
    owner_id = create_user()
    other_id = create_user()

    async with get_db_session() as db_sess:
        moderator = await moderator_service.create(
            make_create(), owner_id, db_sess
        )
        await db_sess.commit()

    with pytest.raises(ModeratorNotFoundException):
        async with get_db_session() as db_sess:
            await moderator_service.get(moderator.id, other_id, db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_raises_when_moderator_missing(moderator_service, create_user):
    user_id = create_user()

    with pytest.raises(ModeratorNotFoundException):
        async with get_db_session() as db_sess:
            await moderator_service.get(uuid.uuid4(), user_id, db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_by_platform_community_returns_moderator(
    moderator_service, create_user
):
    user_id = create_user()
    request = make_create()

    async with get_db_session() as db_sess:
        moderator = await moderator_service.create(request, user_id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await moderator_service.get_by_platform_community(
            request.platform, request.platform_community_id, db_sess
        )

    assert result.id == moderator.id


@pytest.mark.asyncio(loop_scope="session")
async def test_get_by_platform_community_raises_when_missing(
    moderator_service,
):
    with pytest.raises(ModeratorNotFoundException):
        async with get_db_session() as db_sess:
            await moderator_service.get_by_platform_community(
                ModeratorPlatform.DISCORD,
                f"missing-{uuid.uuid4()}",
                db_sess,
            )
