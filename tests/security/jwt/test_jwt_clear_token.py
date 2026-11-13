import pytest

from core.db.session import get_db_session
from user.model import User

from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_clear_token_removes_token_from_user(user_service, jwt_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        await jwt_service.set_token(user, db_sess)
        await jwt_service.clear_token(user, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored.jwt_token is None


@pytest.mark.asyncio(loop_scope="session")
async def test_clear_token_is_idempotent(user_service, jwt_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        await jwt_service.clear_token(user, db_sess)
        await jwt_service.clear_token(user, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)
    assert stored.jwt_token is None
