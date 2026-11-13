import uuid

import pytest
from fastapi import Response

from auth.exception import InvalidCredentialsException
from auth.schema import LoginRequest
from core.db.session import get_db_session
from user.model import User
from user.schema import UserCreate


def _make_create(password="password-1") -> UserCreate:
    suffix = uuid.uuid4().hex
    return UserCreate(
        username=f"user-{suffix}",
        email=f"{suffix}@example.com",
        password=password,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_login_sets_jwt_token_and_cookie(user_service, auth_service):
    req = _make_create()
    async with get_db_session() as db_sess:
        user = await user_service.create(req, db_sess)
        await db_sess.commit()

    rsp = Response()
    async with get_db_session() as db_sess:
        result = await auth_service.login(
            LoginRequest(email=req.email, password=req.password), db_sess, rsp
        )
        await db_sess.commit()

    assert result.id == user.id
    assert result.jwt_token is not None
    assert result.jwt_token.count(".") == 2
    assert "set-cookie" in rsp.headers
    assert result.jwt_token in rsp.headers["set-cookie"]

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored.jwt_token == result.jwt_token


@pytest.mark.asyncio(loop_scope="session")
async def test_login_changes_existing_token(user_service, auth_service):
    req = _make_create()
    async with get_db_session() as db_sess:
        await user_service.create(req, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        first = await auth_service.login(
            LoginRequest(email=req.email, password=req.password), db_sess
        )
        await db_sess.commit()
    first_token = first.jwt_token

    async with get_db_session() as db_sess:
        second = await auth_service.login(
            LoginRequest(email=req.email, password=req.password), db_sess
        )
        await db_sess.commit()

    assert second.jwt_token is not None
    assert second.jwt_token != first_token


@pytest.mark.asyncio(loop_scope="session")
async def test_login_raises_for_wrong_password(user_service, auth_service):
    req = _make_create()
    async with get_db_session() as db_sess:
        user = await user_service.create(req, db_sess)
        await db_sess.commit()

    with pytest.raises(InvalidCredentialsException):
        async with get_db_session() as db_sess:
            await auth_service.login(
                LoginRequest(email=req.email, password="wrong-password"), db_sess
            )

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored.jwt_token is None


@pytest.mark.asyncio(loop_scope="session")
async def test_login_raises_for_unknown_email(user_service, auth_service):
    with pytest.raises(InvalidCredentialsException):
        async with get_db_session() as db_sess:
            await auth_service.login(
                LoginRequest(email="missing@example.com", password="password-1"),
                db_sess,
            )
