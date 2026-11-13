import uuid
from datetime import timedelta

import pytest

from lib.util import get_datetime
from security.jwt.exception import JWTException

from .util import make_service


def test_decode_jwt_returns_payload(jwt_service):
    user_id = uuid.uuid4()
    token = jwt_service.generate_jwt(sub=user_id, em="user@example.com")

    payload = jwt_service.decode_jwt(token)

    assert payload.sub == user_id
    assert payload.em == "user@example.com"


def test_decode_jwt_raises_for_invalid_token(jwt_service):
    with pytest.raises(JWTException):
        jwt_service.decode_jwt("not-a-token")


def test_decode_jwt_raises_for_token_signed_with_other_secret(jwt_service):
    other = make_service(jwt_secret="other-secret-that-is-at-least-32-bytes")
    token = other.generate_jwt(sub=uuid.uuid4(), em="user@example.com")

    with pytest.raises(JWTException):
        jwt_service.decode_jwt(token)


def test_decode_jwt_raises_for_expired_token(jwt_service):
    expiry = int((get_datetime() - timedelta(seconds=1)).timestamp())
    token = jwt_service.generate_jwt(
        sub=uuid.uuid4(), em="user@example.com", exp=expiry
    )

    with pytest.raises(JWTException):
        jwt_service.decode_jwt(token)
