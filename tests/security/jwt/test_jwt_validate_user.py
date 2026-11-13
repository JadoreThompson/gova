import uuid

import pytest

from core.db.session import get_db_session
from security.jwt.exception import JWTException

from .util import make_create


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_user_accepts_current_token(user_service, jwt_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        token = await jwt_service.set_token(user, db_sess)
        await db_sess.commit()

    payload = jwt_service.decode_jwt(token)

    async with get_db_session() as db_sess:
        await jwt_service._validate_user(payload, token, db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_user_raises_when_user_not_found(jwt_service):
    token = jwt_service.generate_jwt(sub=uuid.uuid4(), em="user@example.com")
    payload = jwt_service.decode_jwt(token)

    with pytest.raises(JWTException):
        async with get_db_session() as db_sess:
            await jwt_service._validate_user(payload, token, db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_user_raises_when_user_has_no_token(
    user_service, jwt_service
):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        await db_sess.commit()

    token = jwt_service.generate_jwt(sub=user.id, em=user.email)
    payload = jwt_service.decode_jwt(token)

    with pytest.raises(JWTException):
        async with get_db_session() as db_sess:
            await jwt_service._validate_user(payload, token, db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_user_raises_when_token_does_not_match(
    user_service, jwt_service
):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        old_token = await jwt_service.set_token(user, db_sess)
        await jwt_service.set_token(user, db_sess)
        await db_sess.commit()

    payload = jwt_service.decode_jwt(old_token)

    with pytest.raises(JWTException):
        async with get_db_session() as db_sess:
            await jwt_service._validate_user(payload, old_token, db_sess)
