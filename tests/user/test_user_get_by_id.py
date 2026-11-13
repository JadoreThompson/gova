import uuid

import pytest

from core.db.session import get_db_session
from user.exception import UserNotFoundException

from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_get_returns_user(user_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await user_service.get(user.id, db_sess)

    assert result.id == user.id
    assert result.username == user.username
    assert result.email == user.email


@pytest.mark.asyncio(loop_scope="session")
async def test_get_returns_correct_user_among_many(user_service):
    first = make_create()
    second = make_create()

    async with get_db_session() as db_sess:
        first_user = await user_service.create(first, db_sess)
        second_user = await user_service.create(second, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        result = await user_service.get(second_user.id, db_sess)

    assert result.id == second_user.id
    assert result.id != first_user.id
    assert result.username == second_user.username


@pytest.mark.asyncio(loop_scope="session")
async def test_get_raises_when_user_missing(user_service):
    with pytest.raises(UserNotFoundException):
        async with get_db_session() as db_sess:
            await user_service.get(uuid.uuid4(), db_sess)
