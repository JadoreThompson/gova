from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from security.jwt.service import JWTService
from user.model import User
from user.service import UserService
from .exception import InvalidCredentialsException
from .schema import LoginRequest


class AuthService:
    def __init__(self, user_service: UserService, jwt_service: JWTService) -> None:
        self._user_service = user_service
        self._jwt_service = jwt_service

    async def login(
        self,
        request: LoginRequest,
        db_sess: AsyncSession,
        rsp: Response | None = None,
    ) -> User:
        user = await self._user_service.find_by_email(request.email, db_sess)

        if user is None or not self._user_service.verify_password(
            user, request.password
        ):
            raise InvalidCredentialsException()

        await self._jwt_service.set_cookie(user, db_sess, rsp)
        return user

    async def logout(
        self,
        token: str | User,
        db_sess: AsyncSession,
        rsp: Response | None = None,
    ) -> User:
        if isinstance(token, User):
            user = token
        else:
            payload = await self._jwt_service.validate_jwt(token, db_sess)
            user = await self._user_service.get(payload.sub, db_sess)

        await self._jwt_service.clear_token(user, db_sess)

        if rsp is not None:
            self._jwt_service.remove_cookie(rsp)

        return user
