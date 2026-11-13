import uuid
from unittest.mock import AsyncMock

import pytest

from community.exception import (
    CommunityHasActiveModeratorsException,
    CommunityNotFoundException,
)
from community.model import Community
from core.db.session import get_db_session

from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_removes_community(community_service, create_user):
    community_user_id = create_user()
    async with get_db_session() as db_sess:
        community = await community_service.create(
            make_create(), community_user_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        await community_service.delete(community.id, community_user_id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        comm = await db_sess.get(Community, community.id)

    assert comm is None


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_removes_only_target_community(
    community_service, create_user
):
    community_user_id = create_user()
    async with get_db_session() as db_sess:
        target = await community_service.create(
            make_create(community_id="delete-target"), community_user_id, db_sess
        )
        other = await community_service.create(
            make_create(community_id="delete-other"), community_user_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        await community_service.delete(target.id, community_user_id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        deleted = await db_sess.get(Community, target.id)
        remaining = await db_sess.get(Community, other.id)

    assert deleted is None
    assert remaining is not None
    assert remaining.community_id == "delete-other"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_raises_when_community_missing(
    community_service, create_user
):
    community_user_id = create_user()
    with pytest.raises(CommunityNotFoundException):
        async with get_db_session() as db_sess:
            await community_service.delete(uuid.uuid4(), community_user_id, db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_raises_when_active_moderators_exist(
    community_service, create_user, monkeypatch
):
    community_user_id = create_user()
    async with get_db_session() as db_sess:
        community = await community_service.create(
            make_create(), community_user_id, db_sess
        )
        await db_sess.commit()

    monkeypatch.setattr(
        community_service._moderator_service,
        "has_active_in_community",
        AsyncMock(return_value=True),
    )

    with pytest.raises(CommunityHasActiveModeratorsException):
        async with get_db_session() as db_sess:
            await community_service.delete(community.id, community_user_id, db_sess)
            await db_sess.commit()

    async with get_db_session() as db_sess:
        comm = await db_sess.get(Community, community.id)

    assert comm is not None
