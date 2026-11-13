import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import depends_jwt, get_moderator_service
from core.db.session import get_db_session
from moderator.schema import ModeratorCreate, ModeratorResponse, ModeratorUpdate
from moderator.service import ModeratorService
from security.jwt.schema import JWTPayload

router = APIRouter(prefix="/api/v1/moderators", tags=["Moderators"])


@router.post("/", response_model=ModeratorResponse, status_code=status.HTTP_201_CREATED)
async def create_moderator(
    body: ModeratorCreate,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    moderator = await service.create(body, jwt.sub, db_sess)
    return ModeratorResponse.from_model(moderator)


@router.get("/{id}", response_model=ModeratorResponse)
async def get_moderator(
    id: uuid.UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    moderator = await service.get(id, jwt.sub, db_sess)
    return ModeratorResponse.from_model(moderator)


@router.get("/", response_model=list[ModeratorResponse])
async def list_moderators(
    community_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    moderators, _ = await service.list(
        jwt.sub, db_sess, community_id=community_id, page=page, limit=limit
    )
    return [ModeratorResponse.from_model(m) for m in moderators]


@router.patch("/{id}", response_model=ModeratorResponse)
async def update_moderator(
    id: uuid.UUID,
    body: ModeratorUpdate,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    moderator = await service.update(id, jwt.sub, body, db_sess)
    return ModeratorResponse.from_model(moderator)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_moderator(
    id: uuid.UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: ModeratorService = Depends(get_moderator_service),
):
    await service.delete(id, jwt.sub, db_sess)
