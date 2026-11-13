import uuid

import pytest

from community.exception import CommunityNotFoundException
from core.db.session import get_db_session

from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_get_returns_community(community_service, create_user):
    community_user_id = create_user()
    async with get_db_session() as db_sess:
        community = await community_service.create(make_create(), community_user_id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await community_service.get(community.id, community_user_id, db_sess)

    assert result.id == community.id
    assert result.platform == community.platform
    assert result.community_id == community.community_id
    assert result.policy == community.policy


@pytest.mark.asyncio(loop_scope="session")
async def test_get_returns_correct_community_among_many(
    community_service, create_user
):
    community_user_id = create_user()
    first = make_create(community_id=str(uuid.uuid4()))
    second = make_create(community_id=str(uuid.uuid4()))

    async with get_db_session() as db_sess:
        first_community = await community_service.create(first, community_user_id, db_sess)
        second_community = await community_service.create(second, community_user_id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await community_service.get(second_community.id, community_user_id, db_sess)

    assert result.id == second_community.id
    assert result.id != first_community.id
    assert result.community_id == second_community.community_id


@pytest.mark.asyncio(loop_scope="session")
async def test_get_raises_when_community_missing(
    community_service, create_user
):
    community_user_id = create_user()
    with pytest.raises(CommunityNotFoundException):
        async with get_db_session() as db_sess:
            await community_service.get(uuid.uuid4(), community_user_id, db_sess)
