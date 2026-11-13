import pytest
from sqlalchemy import delete

from core.db.session import get_db_session
from user.model import User

from .util import make_create


async def _clear_users():
    async with get_db_session() as db_sess:
        await db_sess.execute(delete(User))
        await db_sess.commit()


async def _seed_users(user_service, count):
    users = []
    async with get_db_session() as db_sess:
        for _ in range(count):
            users.append(await user_service.create(make_create(), db_sess))
        await db_sess.commit()
    return users


@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_page_and_signals_next_page(user_service):
    await _clear_users()
    users = await _seed_users(user_service, 3)
    expected_ids = {user.id for user in users}

    async with get_db_session() as db_sess:
        page, has_next = await user_service.list(db_sess, page=1, limit=2)

    assert len(page) == 2
    assert {user.id for user in page} <= expected_ids
    assert has_next is True


@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_second_page_without_overlap(user_service):
    await _clear_users()
    users = await _seed_users(user_service, 3)
    expected_ids = {user.id for user in users}

    async with get_db_session() as db_sess:
        first, _ = await user_service.list(db_sess, page=1, limit=2)

    async with get_db_session() as db_sess:
        second, has_next = await user_service.list(db_sess, page=2, limit=2)

    first_ids = {user.id for user in first}
    second_ids = {user.id for user in second}

    assert first_ids | second_ids == expected_ids
    assert first_ids.isdisjoint(second_ids)
    assert has_next is False


@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_everything_when_under_limit(user_service):
    await _clear_users()
    users = await _seed_users(user_service, 2)
    expected_ids = {user.id for user in users}

    async with get_db_session() as db_sess:
        page, has_next = await user_service.list(db_sess, page=1, limit=5)

    assert {user.id for user in page} == expected_ids
    assert has_next is False


@pytest.mark.asyncio(loop_scope="session")
async def test_list_returns_empty_page_when_no_users(user_service):
    await _clear_users()

    async with get_db_session() as db_sess:
        page, has_next = await user_service.list(db_sess, page=1, limit=5)

    assert page == []
    assert has_next is False
