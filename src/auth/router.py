from fastapi import APIRouter, Cookie, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import depends_jwt, get_auth_service, get_twitch_oauth_service
from config import JWT_COOKIE_ALIAS
from core.db.session import get_db_session_dep
from security.jwt.schema import JWTPayload
from .exception import InvalidCredentialsException
from .schema import LoginRequest, PlatformTokenResponse
from .service.auth import AuthService
from .service.twitch import TwitchOAuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    db_sess: AsyncSession = Depends(get_db_session_dep),
    service: AuthService = Depends(get_auth_service),
):
    print('processing login request')
    await service.login(body, db_sess, response)
    response.status_code = 204
    return response


@router.get("/twitch/callback", response_model=PlatformTokenResponse)
async def twitch_callback(
    code: str = Query(..., min_length=1),
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session_dep),
    service: TwitchOAuthService = Depends(get_twitch_oauth_service),
):
    return await service.connect(jwt.sub, code, db_sess)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    token: str | None = Cookie(default=None, alias=JWT_COOKIE_ALIAS),
    db_sess: AsyncSession = Depends(get_db_session_dep),
    service: AuthService = Depends(get_auth_service),
):
    if token is None:
        raise InvalidCredentialsException()

    await service.logout(token, db_sess, response)
