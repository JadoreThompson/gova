import uuid

import pytest
from pydantic import ValidationError

from community.enums import CommunityPlatform
from community.exception import CommunityAlreadyExistsException
from community.model import Community
from community.schema import CommunityResponse
from core.db.session import get_db_session
from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_create_adds_community_and_returns_it(community_service, create_user):
    community_user_id = create_user()
    req = make_create()
    async with get_db_session() as db_sess:
        community = await community_service.create(req, community_user_id, db_sess)
        await db_sess.commit()

    assert isinstance(community, CommunityResponse)
    assert community.platform == CommunityPlatform.DISCORD
    assert community.community_id == req.community_id
    assert community.policy == "Be nice."

    async with get_db_session() as db_sess:
        comm = await db_sess.get(Community, community.id)

    assert comm is not None


@pytest.mark.asyncio(loop_scope="session")
async def test_create_raises_when_community_already_exists(
    community_service, create_user
):
    community_user_id = create_user()
    req = make_create()

    async with get_db_session() as db_sess:
        community = await community_service.create(req, community_user_id, db_sess)
        await db_sess.commit()

    new_req = req.model_copy()
    new_req.policy = "our new policy"

    with pytest.raises(CommunityAlreadyExistsException):
        async with get_db_session() as db_sess:
            await community_service.create(new_req, community_user_id, db_sess)
            await db_sess.commit()

    async with get_db_session() as db_sess:
        comm = await db_sess.get(Community, community.id)

    assert comm.policy == req.policy


@pytest.mark.asyncio(loop_scope="session")
async def test_create_does_not_raise_for_different_community_ids(
    community_service, create_user
):
    community_user_id = create_user()
    first = make_create(community_id=str(uuid.uuid4()))
    second = make_create(community_id=str(uuid.uuid4()))

    async with get_db_session() as db_sess:
        first_community = await community_service.create(
            first, community_user_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        second_community = await community_service.create(
            second, community_user_id, db_sess
        )
        await db_sess.commit()

    assert first_community.id != second_community.id
    assert first_community.community_id != second_community.community_id


@pytest.mark.asyncio(loop_scope="session")
async def test_create_does_not_raise_for_same_id_on_other_platform(
    community_service, create_user
):
    community_user_id = create_user()
    community_id = str(uuid.uuid4())

    async with get_db_session() as db_sess:
        discord = await community_service.create(
            make_create(platform=CommunityPlatform.DISCORD, community_id=community_id),
            community_user_id,
            db_sess,
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        youtube = await community_service.create(
            make_create(platform=CommunityPlatform.YOUTUBE, community_id=community_id),
            community_user_id,
            db_sess,
        )
        await db_sess.commit()

    assert discord.id != youtube.id
    assert discord.platform == CommunityPlatform.DISCORD
    assert youtube.platform == CommunityPlatform.YOUTUBE
    assert discord.community_id == youtube.community_id == community_id


def test_create_does_not_raise_for_single_character_policy():
    request = make_create(policy="a")

    assert request.policy == "a"


def test_create_raises_validation_error_when_policy_is_blank():
    with pytest.raises(ValidationError):
        make_create(policy="   ")


def test_create_raises_validation_error_when_community_id_is_empty():
    with pytest.raises(ValidationError):
        make_create(community_id="")


def test_create_does_not_raise_for_minimal_valid_payload():
    request = make_create(policy="abc")

    assert request.policy == "abc"
