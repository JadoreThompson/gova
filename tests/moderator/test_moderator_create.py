import uuid

import pytest

from core.db.session import get_db_session
from moderator.enums import ModeratorPlatform, ModeratorStatus
from moderator.exception import ModeratorAlreadyExistsException
from moderator.model import Moderator
from moderator.schema import ModeratorCreate, ModeratorResponse
from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_create_links_moderator_to_user_and_community(
    moderator_service, create_user
):
    user_id = create_user()
    request = make_create()

    async with get_db_session() as db_sess:
        moderator = await moderator_service.create(request, user_id, db_sess)
        await db_sess.commit()

    assert isinstance(moderator, ModeratorResponse)
    assert moderator.platform == request.platform
    assert moderator.platform_community_id == request.platform_community_id
    assert moderator.community_policy == request.community_policy
    assert moderator.name == "Moderator"
    assert moderator.status == ModeratorStatus.OFFLINE

    async with get_db_session() as db_sess:
        stored = await db_sess.get(Moderator, moderator.id)

    assert stored is not None
    assert stored.user_id == user_id


@pytest.mark.asyncio(loop_scope="session")
async def test_create_raises_when_community_already_has_moderator(
    moderator_service, create_user
):
    user_id = create_user()
    request = make_create()

    async with get_db_session() as db_sess:
        await moderator_service.create(request, user_id, db_sess)
        await db_sess.commit()

    with pytest.raises(ModeratorAlreadyExistsException):
        async with get_db_session() as db_sess:
            await moderator_service.create(
                make_create(
                    platform=request.platform,
                    platform_community_id=request.platform_community_id,
                    community_policy="Another policy.",
                ),
                create_user(),
                db_sess,
            )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_rejects_duplicate_for_different_policy(
    moderator_service, create_user
):
    user_id = create_user()
    request = make_create()

    async with get_db_session() as db_sess:
        await moderator_service.create(request, user_id, db_sess)
        await db_sess.commit()

    with pytest.raises(ModeratorAlreadyExistsException):
        async with get_db_session() as db_sess:
            await moderator_service.create(
                request.model_copy(update={"community_policy": "Changed."}),
                user_id,
                db_sess,
            )


@pytest.mark.asyncio(loop_scope="session")
async def test_create_allows_same_community_on_other_platform(
    moderator_service, create_user
):
    user_id = create_user()
    community_id = f"community-{uuid.uuid4()}"

    async with get_db_session() as db_sess:
        discord = await moderator_service.create(
            make_create(
                platform=ModeratorPlatform.DISCORD,
                platform_community_id=community_id,
            ),
            user_id,
            db_sess,
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        youtube = await moderator_service.create(
            make_create(
                platform=ModeratorPlatform.YOUTUBE,
                platform_community_id=community_id,
            ),
            user_id,
            db_sess,
        )
        await db_sess.commit()

    assert discord.id != youtube.id
    assert discord.platform == ModeratorPlatform.DISCORD
    assert youtube.platform == ModeratorPlatform.YOUTUBE
    assert discord.platform_community_id == youtube.platform_community_id


def test_create_payload_does_not_accept_user_id():
    assert "user_id" not in ModeratorCreate.model_fields


def test_response_does_not_expose_user_id():
    assert "user_id" not in ModeratorResponse.model_fields
