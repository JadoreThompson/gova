import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import depends_jwt, get_community_service
from core.db.session import get_db_session
from security.jwt.schema import JWTPayload
from .schema import CommunityCreate, CommunityResponse, CommunityUpdate
from .service import CommunityService

router = APIRouter(prefix="/api/v1/communities", tags=["Communities"])


@router.post("/", response_model=CommunityResponse, status_code=status.HTTP_201_CREATED)
async def create_community(
    body: CommunityCreate,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: CommunityService = Depends(get_community_service),
):
    community = await service.create(body, jwt.sub, db_sess)
    return community


@router.get("/{id}", response_model=CommunityResponse)
async def get_community(
    id: uuid.UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: CommunityService = Depends(get_community_service),
):
    community = await service.get(id, jwt.sub, db_sess)
    return community


@router.get("/", response_model=list[CommunityResponse])
async def list_communities(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: CommunityService = Depends(get_community_service),
):
    communities, _ = await service.list(jwt.sub, db_sess, page=page, limit=limit)
    return communities


@router.patch("/{id}", response_model=CommunityResponse)
async def update_community(
    id: uuid.UUID,
    body: CommunityUpdate,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: CommunityService = Depends(get_community_service),
):
    community = await service.update(id, jwt.sub, body, db_sess)
    return community


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_community(
    id: uuid.UUID,
    jwt: JWTPayload = Depends(depends_jwt),
    db_sess: AsyncSession = Depends(get_db_session),
    service: CommunityService = Depends(get_community_service),
):
    await service.delete(id, jwt.sub, db_sess)
