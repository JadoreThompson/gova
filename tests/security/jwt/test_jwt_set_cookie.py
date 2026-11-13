import pytest
from fastapi import Response

from core.db.session import get_db_session

from .util import make_create, make_service


@pytest.mark.asyncio(loop_scope="session")
async def test_set_cookie_sets_token_and_cookie(user_service, jwt_service):
    rsp = Response()
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        result = await jwt_service.set_cookie(user, db_sess, rsp)
        await db_sess.commit()

    assert result is rsp
    assert user.jwt_token is not None
    assert "set-cookie" in result.headers
    assert jwt_service.cookie_alias in result.headers["set-cookie"]
    assert user.jwt_token in result.headers["set-cookie"]


@pytest.mark.asyncio(loop_scope="session")
async def test_set_cookie_creates_response_when_omitted(user_service, jwt_service):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        result = await jwt_service.set_cookie(user, db_sess)
        await db_sess.commit()

    assert isinstance(result, Response)
    assert "set-cookie" in result.headers
    assert jwt_service.cookie_alias in result.headers["set-cookie"]


@pytest.mark.asyncio(loop_scope="session")
async def test_set_cookie_marks_cookie_secure_in_production(user_service):
    service = make_service(is_production=True)
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        result = await service.set_cookie(user, db_sess)
        await db_sess.commit()

    cookie = result.headers["set-cookie"].lower()

    assert "httponly" in cookie
    assert "secure" in cookie


@pytest.mark.asyncio(loop_scope="session")
async def test_set_cookie_does_not_mark_cookie_secure_outside_production(
    user_service, jwt_service
):
    async with get_db_session() as db_sess:
        user = await user_service.create(make_create(), db_sess)
        result = await jwt_service.set_cookie(user, db_sess)
        await db_sess.commit()

    assert "secure" not in result.headers["set-cookie"].lower()
