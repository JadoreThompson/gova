import pytest

from core.db.session import get_db_session
from moderator.exception import ModeratorNotFoundException
from moderator.model import Moderators
from .util import make_community, make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_removes_moderator(
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
        await moderator_service.delete(moderator.id, user_id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        stored = await db_sess.get(Moderators, moderator.id)

    assert stored is None


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_raises_when_moderator_belongs_to_another_user(
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
            await moderator_service.delete(moderator.id, other_id, db_sess)

    async with get_db_session() as db_sess:
        stored = await db_sess.get(Moderators, moderator.id)

    assert stored is not None
