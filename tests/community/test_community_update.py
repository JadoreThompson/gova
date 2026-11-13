import uuid

import pytest
from pydantic import ValidationError

from community.exception import CommunityNotFoundException
from community.model import Community
from community.schema import CommunityUpdate
from core.db.session import get_db_session

from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_update_changes_policy(community_service, create_user):
    community_user_id = create_user()
    async with get_db_session() as db_sess:
        community = await community_service.create(
            make_create(policy="Be nice."), community_user_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await community_service.update(
            community.id,
            community_user_id,
            CommunityUpdate(policy="Stay on topic."),
            db_sess,
        )
        await db_sess.commit()

    assert result.id == community.id
    assert result.policy == "Stay on topic."

    async with get_db_session() as db_sess:
        comm = await db_sess.get(Community, community.id)

    assert comm is not None
    assert comm.policy == "Stay on topic."


@pytest.mark.asyncio(loop_scope="session")
async def test_update_keeps_policy_when_not_provided(
    community_service, create_user
):
    community_user_id = create_user()
    async with get_db_session() as db_sess:
        community = await community_service.create(
            make_create(policy="Be nice."), community_user_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await community_service.update(
            community.id, community_user_id, CommunityUpdate(), db_sess
        )
        await db_sess.commit()

    assert result.id == community.id
    assert result.policy == "Be nice."


@pytest.mark.asyncio(loop_scope="session")
async def test_update_does_not_change_other_communities(
    community_service, create_user
):
    community_user_id = create_user()
    async with get_db_session() as db_sess:
        first = await community_service.create(
            make_create(policy="First policy."), community_user_id, db_sess
        )
        second = await community_service.create(
            make_create(policy="Second policy."), community_user_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        await community_service.update(
            first.id,
            community_user_id,
            CommunityUpdate(policy="Updated policy."),
            db_sess,
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        unchanged = await db_sess.get(Community, second.id)

    assert unchanged.policy == "Second policy."


@pytest.mark.asyncio(loop_scope="session")
async def test_update_raises_when_community_missing(
    community_service, create_user
):
    community_user_id = create_user()
    with pytest.raises(CommunityNotFoundException):
        async with get_db_session() as db_sess:
            await community_service.update(
                uuid.uuid4(),
                community_user_id,
                CommunityUpdate(policy="Stay on topic."),
                db_sess,
            )


@pytest.mark.asyncio(loop_scope="session")
async def test_update_trims_policy_whitespace(
    community_service, create_user
):
    community_user_id = create_user()
    async with get_db_session() as db_sess:
        community = await community_service.create(make_create(), community_user_id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await community_service.update(
            community.id,
            community_user_id,
            CommunityUpdate(policy="  Stay on topic.  "),
            db_sess,
        )
        await db_sess.commit()

    assert result.policy == "Stay on topic."


def test_update_does_not_raise_for_single_character_policy():
    request = CommunityUpdate(policy="a")

    assert request.policy == "a"


def test_update_does_not_raise_for_minimal_valid_payload():
    request = CommunityUpdate(policy="abc")

    assert request.policy == "abc"


def test_update_raises_validation_error_when_policy_is_blank():
    with pytest.raises(ValidationError):
        CommunityUpdate(policy="   ")


def test_update_raises_validation_error_when_policy_is_empty():
    with pytest.raises(ValidationError):
        CommunityUpdate(policy="")
