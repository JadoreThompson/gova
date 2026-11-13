from argon2 import PasswordHasher
from fastapi import Request
from fastapi import Depends

from auth.service import AuthService
from community.service import CommunityService
from config import JWT_COOKIE_ALIAS
from moderator.service import ModeratorService
from security.jwt.exception import JWTException
from security.jwt.schema import JWTPayload
from security.jwt.service import JWTService
from user.service import UserService


def get_user_service() -> UserService:
    return UserService(PasswordHasher())


def get_moderator_service() -> ModeratorService:
    return ModeratorService()


def get_community_service(
    moderator_service: ModeratorService = Depends(get_moderator_service),
) -> CommunityService:
    return CommunityService(moderator_service)


def get_jwt_service() -> JWTService:
    return JWTService()


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> AuthService:
    return AuthService(user_service, jwt_service)


async def depends_jwt(req: Request) -> JWTPayload:
    token = req.cookies.get(JWT_COOKIE_ALIAS)
    if not token:
        raise JWTException("Authentication token is missing")

    return await get_jwt_service().validate_jwt(token)
