from .util import make_service


def test_cookie_alias_returns_configured_alias(jwt_service):
    assert jwt_service.cookie_alias == "test-cookie"


def test_cookie_alias_reflects_custom_alias():
    service = make_service(cookie_alias="custom-cookie")

    assert service.cookie_alias == "custom-cookie"
