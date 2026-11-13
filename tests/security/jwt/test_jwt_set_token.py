import pytest

from core.db.session import get_db_session

from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_set_token_stores_token_on_user(user_service, jwt_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        token = await jwt_service.set_token(user, db_sess)
        await db_sess.commit()

    assert token
    assert user.jwt_token == token

    async with get_db_session() as db_sess:
        stored = await db_sess.get(type(user), user.id)

    assert stored.jwt_token == token


@pytest.mark.asyncio(loop_scope="session")
async def test_set_token_encodes_user_identity(user_service, jwt_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        token = await jwt_service.set_token(user, db_sess)
        await db_sess.commit()

    payload = jwt_service.decode_jwt(token)

    assert payload.sub == user.id
    assert payload.em == user.email


@pytest.mark.asyncio(loop_scope="session")
async def test_set_token_replaces_existing_token(user_service, jwt_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        first = await jwt_service.set_token(user, db_sess)
        second = await jwt_service.set_token(user, db_sess)
        await db_sess.commit()

    assert second
    assert second != first
    assert user.jwt_token == second
