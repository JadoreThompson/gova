import uuid
from datetime import timedelta

import pytest

from core.db.session import get_db_session
from lib.util import get_datetime
from security.jwt.exception import JWTException

from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_jwt_accepts_current_token(user_service, jwt_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        token = await jwt_service.set_token(user, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        payload = await jwt_service.validate_jwt(token, db_sess)

    assert payload.sub == user.id
    assert payload.em == user.email


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_jwt_rejects_replaced_token(user_service, jwt_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        old_token = await jwt_service.set_token(user, db_sess)
        await jwt_service.set_token(user, db_sess)
        await db_sess.commit()

    with pytest.raises(JWTException):
        async with get_db_session() as db_sess:
            await jwt_service.validate_jwt(old_token, db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_jwt_rejects_token_after_logout(user_service, jwt_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        token = await jwt_service.set_token(user, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        loaded = await db_sess.get(type(user), user.id)
        await jwt_service.clear_token(loaded, db_sess)
        await db_sess.commit()

    with pytest.raises(JWTException):
        async with get_db_session() as db_sess:
            await jwt_service.validate_jwt(token, db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_jwt_rejects_unknown_user(jwt_service):
    token = jwt_service.generate_jwt(sub=uuid.uuid4(), em="user@example.com")

    with pytest.raises(JWTException):
        async with get_db_session() as db_sess:
            await jwt_service.validate_jwt(token, db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_jwt_rejects_expired_token(user_service, jwt_service):
    expiry = int((get_datetime() - timedelta(seconds=1)).timestamp())

    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        token = jwt_service.generate_jwt(
            sub=user.id, em=user.email, exp=expiry
        )
        user.jwt_token = token
        await db_sess.commit()

    with pytest.raises(JWTException):
        async with get_db_session() as db_sess:
            await jwt_service.validate_jwt(token, db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_jwt_rejects_invalid_token(jwt_service):
    with pytest.raises(JWTException):
        await jwt_service.validate_jwt("not-a-token")


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_jwt_opens_session_when_omitted(user_service, jwt_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        token = await jwt_service.set_token(user, db_sess)
        await db_sess.commit()

    payload = await jwt_service.validate_jwt(token)

    assert payload.sub == user.id
