import uuid

from lib.util import get_datetime
from security.jwt.schema import JWTPayload


def test_generate_jwt_round_trips_payload(jwt_service):
    user_id = uuid.uuid4()

    token = jwt_service.generate_jwt(sub=user_id, em="user@example.com")
    payload = jwt_service.decode_jwt(token)

    assert isinstance(payload, JWTPayload)
    assert payload.sub == user_id
    assert payload.em == "user@example.com"
    assert payload.exp > int(get_datetime().timestamp())


def test_generate_jwt_accepts_string_subject(jwt_service):
    user_id = uuid.uuid4()

    token = jwt_service.generate_jwt(sub=str(user_id), em="user@example.com")
    payload = jwt_service.decode_jwt(token)

    assert payload.sub == user_id


def test_generate_jwt_uses_supplied_expiry(jwt_service):
    expiry = int(get_datetime().timestamp()) + 60

    token = jwt_service.generate_jwt(
        sub=uuid.uuid4(), em="user@example.com", exp=expiry
    )
    payload = jwt_service.decode_jwt(token)

    assert payload.exp == expiry


def test_generate_jwt_produces_unique_tokens(jwt_service):
    user_id = uuid.uuid4()

    first = jwt_service.decode_jwt(
        jwt_service.generate_jwt(sub=user_id, em="user@example.com")
    )
    second = jwt_service.decode_jwt(
        jwt_service.generate_jwt(sub=user_id, em="user@example.com")
    )

    assert first.jti != second.jti


def test_generate_jwt_returns_three_segment_token(jwt_service):
    token = jwt_service.generate_jwt(
        sub=uuid.uuid4(), em="user@example.com"
    )

    assert token.count(".") == 2
