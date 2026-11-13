from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import JWT_COOKIE_ALIAS
from core.db.session import get_db_session
from api.deps import get_auth_service
from .exception import InvalidCredentialsException
from .schema import LoginRequest, LoginResponse
from .service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db_sess: AsyncSession = Depends(get_db_session),
    service: AuthService = Depends(get_auth_service),
):
    await service.login(body, db_sess, response)
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    token: str | None = Cookie(default=None, alias=JWT_COOKIE_ALIAS),
    db_sess: AsyncSession = Depends(get_db_session),
    service: AuthService = Depends(get_auth_service),
):
    if token is None:
        raise InvalidCredentialsException()

    await service.logout(token, db_sess, response)
