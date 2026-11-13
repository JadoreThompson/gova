import uuid

import pytest

from core.db.session import get_db_session
from moderator.exception import ModeratorNotFoundException
from .util import make_community, make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_get_returns_moderator(
    moderator_service, community_service, create_user
):
    user_id = create_user()
    community = await make_community(community_service, user_id)

    async with get_db_session() as db_sess:
        moderator = await moderator_service.create(
            make_create(community.id), user_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await moderator_service.get(moderator.id, user_id, db_sess)

    assert result.id == moderator.id
    assert result.community_id == community.id


@pytest.mark.asyncio(loop_scope="session")
async def test_get_raises_when_moderator_belongs_to_another_user(
    moderator_service, community_service, create_user
):
    owner_id = create_user()
    other_id = create_user()
    community = await make_community(community_service, owner_id)

    async with get_db_session() as db_sess:
        moderator = await moderator_service.create(
            make_create(community.id), owner_id, db_sess
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
