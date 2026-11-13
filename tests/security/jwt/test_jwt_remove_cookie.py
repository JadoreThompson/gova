from fastapi import Response

from .util import make_service


def test_remove_cookie_deletes_cookie(jwt_service):
    rsp = Response()

    result = jwt_service.remove_cookie(rsp)

    assert result is rsp
    assert "set-cookie" in result.headers
    assert jwt_service.cookie_alias in result.headers["set-cookie"]


def test_remove_cookie_creates_response_when_omitted(jwt_service):
    result = jwt_service.remove_cookie()

    assert isinstance(result, Response)
    assert "set-cookie" in result.headers
    assert jwt_service.cookie_alias in result.headers["set-cookie"]


def test_remove_cookie_marks_cookie_secure_in_production():
    service = make_service(is_production=True)

    result = service.remove_cookie()
    cookie = result.headers["set-cookie"].lower()

    assert "httponly" in cookie
    assert "secure" in cookie
