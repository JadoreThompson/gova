import uuid

from security.jwt.service import JWTService
from user.schema import UserCreate


def make_create(**overrides) -> UserCreate:
    suffix = uuid.uuid4().hex
    values = {
        "username": f"user-{suffix}",
        "email": f"{suffix}@example.com",
        "password": "password-1",
    }
    values.update(overrides)
    return UserCreate(**values)


def make_service(**overrides) -> JWTService:
    values = {
        "jwt_secret": "test-secret-that-is-at-least-32-bytes-long",
        "jwt_algo": "HS256",
        "jwt_expiry_secs": 3600,
        "cookie_alias": "test-cookie",
        "is_production": False,
    }
    values.update(overrides)
    return JWTService(**values)
