from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import depends_jwt, get_user_service
from core.db.session import get_db_session
from security.jwt.schema import JWTPayload
from .schema import UserResponse
from .service import UserService

router = APIRouter(prefix="/api/v1", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: UserService = Depends(get_user_service),
):
    user = await service.get(jwt.sub, db_sess)
    return UserResponse.from_model(user)
