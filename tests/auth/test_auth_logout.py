import uuid

import pytest
from fastapi import Response

from auth.schema import LoginRequest
from core.db.session import get_db_session
from security.jwt.exception import JWTException
from user.model import User
from user.schema import UserCreate


def _make_create() -> UserCreate:
    suffix = uuid.uuid4().hex
    return UserCreate(
        username=f"user-{suffix}",
        email=f"{suffix}@example.com",
        password="password-1",
    )


async def _login(user_service, auth_service, db_sess):
    req = _make_create()
    await user_service.create(req, db_sess)
    user = await auth_service.login(
        LoginRequest(email=req.email, password=req.password), db_sess
    )
    await db_sess.commit()
    return user


@pytest.mark.asyncio(loop_scope="session")
async def test_logout_clears_jwt_token(user_service, auth_service):
    async with get_db_session() as db_sess:
        user = await _login(user_service, auth_service, db_sess)

    async with get_db_session() as db_sess:
        loaded = await db_sess.get(User, user.id)
        token = loaded.jwt_token
        await auth_service.logout(token, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored.jwt_token is None


@pytest.mark.asyncio(loop_scope="session")
async def test_logout_deletes_cookie(user_service, auth_service):
    async with get_db_session() as db_sess:
        user = await _login(user_service, auth_service, db_sess)

    rsp = Response()
    async with get_db_session() as db_sess:
        loaded = await db_sess.get(User, user.id)
        await auth_service.logout(loaded.jwt_token, db_sess, rsp)
        await db_sess.commit()

    assert "set-cookie" in rsp.headers
    assert loaded.jwt_token is None


@pytest.mark.asyncio(loop_scope="session")
async def test_logout_clears_token_when_given_valid_token(user_service, auth_service):
    async with get_db_session() as db_sess:
        user = await _login(user_service, auth_service, db_sess)

    async with get_db_session() as db_sess:
        loaded = await db_sess.get(User, user.id)
        await auth_service.logout(loaded.jwt_token, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored.jwt_token is None


@pytest.mark.asyncio(loop_scope="session")
async def test_logout_rejects_invalid_token(auth_service):
    with pytest.raises(JWTException):
        async with get_db_session() as db_sess:
            await auth_service.logout("not-a-token", db_sess)


@pytest.mark.asyncio(loop_scope="session")
async def test_logout_rejects_stale_token(user_service, auth_service):
    async with get_db_session() as db_sess:
        user = await _login(user_service, auth_service, db_sess)
        user_id = user.id

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user_id)
        old_token = stored.jwt_token

    async with get_db_session() as db_sess:
        loaded = await db_sess.get(User, user_id)
        await auth_service.login(
            LoginRequest(email=loaded.email, password="password-1"),
            db_sess,
        )
        await db_sess.commit()

    with pytest.raises(JWTException):
        async with get_db_session() as db_sess:
            await auth_service.logout(old_token, db_sess)
