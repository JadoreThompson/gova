from typing import Type, TypeVar, cast

from argon2 import PasswordHasher
from fastapi import Depends, Request

from auth.service import AuthService
from community.service import CommunityService
from config import JWT_COOKIE_ALIAS
from event.publisher import AIOKafkaEventPublisher, EventPublisher
from moderator.service.moderator import ModeratorService
from security.jwt.exception import JWTException
from security.jwt.schema import JWTPayload
from security.jwt.service import JWTService
from user.service import UserService

V = TypeVar("V")

_REGISTRY: dict[Type, object] = {}


def _get_or_create_object(cls: Type[V], *args, **kwargs) -> V:
    if cls not in _REGISTRY:
        _REGISTRY[cls] = cls(*args, **kwargs)

    return cast(V, _REGISTRY[cls])


def get_user_service() -> UserService:
    return _get_or_create_object(UserService, _get_or_create_object(PasswordHasher))


def get_event_publisher() -> EventPublisher:
    return _get_or_create_object(AIOKafkaEventPublisher)


def get_moderator_service(
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> ModeratorService:
    return _get_or_create_object(ModeratorService, event_publisher)


def get_community_service(
    moderator_service: ModeratorService = Depends(get_moderator_service),
) -> CommunityService:
    return _get_or_create_object(CommunityService, moderator_service)


def get_jwt_service() -> JWTService:
    return _get_or_create_object(JWTService)


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> AuthService:
    return _get_or_create_object(AuthService, user_service, jwt_service)


async def depends_jwt(req: Request) -> JWTPayload:
    token = req.cookies.get(JWT_COOKIE_ALIAS)
    if not token:
        raise JWTException("Authentication token is missing")

    return await get_jwt_service().validate_jwt(token)
