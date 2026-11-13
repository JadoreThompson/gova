import uuid

import pytest
from fastapi import Response

from auth.exception import InvalidCredentialsException
from auth.schema import LoginRequest
from core.db.session import get_db_session
from user.model import User
from user.schema import UserCreate, UserResponse


def _token_from_cookie(response: Response) -> str:
    return response.headers["set-cookie"].split(";", 1)[0].split("=", 1)[1]


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
    assert isinstance(result, UserResponse)
    token = _token_from_cookie(rsp)
    assert token.count(".") == 2
    assert "set-cookie" in rsp.headers
    assert token in rsp.headers["set-cookie"]

    async with get_db_session() as db_sess:
        stored = await db_sess.get(User, user.id)

    assert stored.jwt_token == token


@pytest.mark.asyncio(loop_scope="session")
async def test_login_changes_existing_token(user_service, auth_service):
    req = _make_create()
    async with get_db_session() as db_sess:
        await user_service.create(req, db_sess)
        await db_sess.commit()

    async with get_db_session() as db_sess:
        first_response = Response()
        first = await auth_service.login(
            LoginRequest(email=req.email, password=req.password), db_sess, first_response
        )
        await db_sess.commit()
    first_token = _token_from_cookie(first_response)

    async with get_db_session() as db_sess:
        second_response = Response()
        second = await auth_service.login(
            LoginRequest(email=req.email, password=req.password),
            db_sess,
            second_response,
        )
        await db_sess.commit()

    second_token = _token_from_cookie(second_response)
    assert second.id == first.id
    assert second_token != first_token


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
