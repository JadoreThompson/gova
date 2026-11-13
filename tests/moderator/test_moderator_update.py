import pytest

from core.db.session import get_db_session
from moderator.exception import ModeratorNotFoundException
from moderator.model import Moderators
from moderator.schema import ModeratorUpdate
from .util import make_community, make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_update_changes_moderator(
    moderator_service, community_service, create_user
):
    user_id = create_user()
    community = await make_community(community_service, user_id)

    async with get_db_session() as db_sess:
        moderator = await moderator_service.create(
            make_create(community.id, name="Old"), user_id, db_sess
        )
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await moderator_service.update(
            moderator.id,
            user_id,
            ModeratorUpdate(name="New"),
            db_sess,
        )
        await db_sess.commit()

    assert result.name == "New"

    async with get_db_session() as db_sess:
        stored = await db_sess.get(Moderators, moderator.id)

    assert stored.name == "New"


@pytest.mark.asyncio(loop_scope="session")
async def test_update_raises_when_moderator_belongs_to_another_user(
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
            await moderator_service.update(
                moderator.id, other_id, ModeratorUpdate(name="Hacked"), db_sess
            )
