import logging
from datetime import timedelta

import jwt
from fastapi import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import (
    IS_PRODUCTION,
    JWT_ALGO,
    JWT_COOKIE_ALIAS,
    JWT_EXPIRY_SECS,
    JWT_SECRET,
)
from lib.util import get_datetime
from user.model import User
from .exception import JWTException
from .schema import JWTPayload


class JWTService:
    def __init__(
        self,
        jwt_secret: str = JWT_SECRET,
        jwt_algo: str = JWT_ALGO,
        jwt_expiry_secs: int = JWT_EXPIRY_SECS,
        cookie_alias: str = JWT_COOKIE_ALIAS,
        is_production: bool = IS_PRODUCTION,
    ):
        self._jwt_secret = jwt_secret
        self._jwt_algo = jwt_algo
        self._jwt_expiry_secs = jwt_expiry_secs
        self._cookie_alias = cookie_alias
        self._is_production = is_production
        self._logger = logging.getLogger("jwt_service")

    @property
    def cookie_alias(self) -> str:
        return self._cookie_alias

    def _generate_expiry(self) -> int:
        """Private method to generate JWT expiry datetime"""
        return int(
            (get_datetime() + timedelta(seconds=self._jwt_expiry_secs)).timestamp()
        )

    def generate_jwt(self, **kwargs) -> str:
        """Generates a JWT token"""
        if kwargs.get("exp") is None:
            kwargs["exp"] = self._generate_expiry()

        kwargs["sub"] = str(kwargs["sub"])

        payload = JWTPayload(**kwargs)

        return jwt.encode(
            payload.model_dump(mode="json"), self._jwt_secret, algorithm=self._jwt_algo
        )

    def decode_jwt(self, token: str) -> JWTPayload:
        try:
            return JWTPayload(
                **jwt.decode(
                    token,
                    self._jwt_secret,
                    algorithms=[self._jwt_algo],
                )
            )
        except jwt.ExpiredSignatureError:
            raise JWTException("Token has expired")
        except jwt.InvalidTokenError:
            raise JWTException("Invalid token")

    async def set_token(self, user: User, db_sess: AsyncSession) -> str:
        token = self.generate_jwt(sub=user.id, em=user.email)
        user.jwt_token = token
        await db_sess.flush()
        return token

    async def clear_token(self, user: User, db_sess: AsyncSession) -> None:
        user.jwt_token = None
        await db_sess.flush()

    async def set_cookie(
        self, user: User, db_sess: AsyncSession, rsp: Response | None = None
    ) -> Response:
        token = await self.set_token(user, db_sess)

        if rsp is None:
            rsp = Response()

        rsp.set_cookie(
            self._cookie_alias,
            token,
            httponly=True,
            secure=self._is_production,
            expires=self._generate_expiry(),
        )

        return rsp

    def remove_cookie(self, rsp: Response | None = None) -> Response:
        if rsp is None:
            rsp = Response()

        rsp.delete_cookie(
            self._cookie_alias,
            httponly=True,
            secure=self._is_production,
        )

        return rsp

    async def validate_jwt(
        self, token: str, db_sess: AsyncSession | None = None
    ) -> JWTPayload:
        """Validate a JWT token and ensure the User exists.

        Args:
            token (str): JWT token to validate.
            db_sess (AsyncSession | None): Session to use. A new session is
                opened when omitted.

        Raises:
            JWTException: The token is invalid, expired, or no longer current.

        Returns:
            JWTPayload: Original payload
        """
        payload = self.decode_jwt(token)

        if payload.exp < int(get_datetime().timestamp()):
            raise JWTException("Expired token")

        if db_sess is not None:
            await self._validate_user(payload, token, db_sess)
            return payload

        from core.db.session import get_db_session

        async with get_db_session() as session:
            await self._validate_user(payload, token, session)

        return payload

    async def _validate_user(
        self, payload: JWTPayload, token: str, db_sess: AsyncSession
    ) -> None:
        user = await db_sess.scalar(select(User).where(User.id == payload.sub))

        if user is None:
            raise JWTException("User not found.")

        if user.jwt_token is None or user.jwt_token != token:
            raise JWTException("Invalid token")
