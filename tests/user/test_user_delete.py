import uuid

import pytest

from core.db.session import get_db_session
from user.exception import UserNotFoundException
from user.model import User

from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_removes_user(user_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        await user_service.delete(user.id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored is None


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_removes_only_target_user(user_service):
    async with get_db_session() as db_sess:
        target = await user_service.create(make_create(), db_sess)
        other = await user_service.create(make_create(), db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        await user_service.delete(target.id, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        deleted = await db_sess.get(User, target.id)
        remaining = await db_sess.get(User, other.id)

    assert deleted is None
    assert remaining is not None
    assert remaining.username == other.username


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_raises_when_user_missing(user_service):
    with pytest.raises(UserNotFoundException):
        async with get_db_session() as db_sess:
            await user_service.delete(uuid.uuid4(), db_sess)
