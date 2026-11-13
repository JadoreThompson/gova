import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from moderator.service import ModeratorService
from .exception import (
    CommunityAlreadyExistsException,
    CommunityHasActiveModeratorsException,
    CommunityNotFoundException,
)
from .model import Community
from .schema import CommunityCreate, CommunityResponse, CommunityUpdate


class CommunityService:
    def __init__(self, moderator_service: ModeratorService) -> None:
        self._moderator_service = moderator_service

    async def create(
        self, request: CommunityCreate, user_id: uuid.UUID, db_sess: AsyncSession
    ) -> CommunityResponse:
        existing = await db_sess.scalar(
            select(Community).where(
                Community.platform == request.platform,
                Community.community_id == request.community_id,
            )
        )
        if existing is not None:
            raise CommunityAlreadyExistsException()

        community = Community(
            user_id=user_id,
            platform=request.platform,
            community_id=request.community_id,
            policy=request.policy,
        )
        db_sess.add(community)
        await db_sess.flush()
        await db_sess.refresh(community)
        return CommunityResponse.from_model(community)

    async def get(
        self, id: uuid.UUID, user_id: uuid.UUID, db_sess: AsyncSession
    ) -> CommunityResponse:
        community = await db_sess.scalar(
            select(Community).where(
                Community.id == id,
                Community.user_id == user_id,
            )
        )
        if community is None:
            raise CommunityNotFoundException()
        return CommunityResponse.from_model(community)

    async def get_by_id(
        self, id: uuid.UUID, db_sess: AsyncSession
    ) -> CommunityResponse:
        community = await db_sess.get(Community, id)
        if community is None:
            raise CommunityNotFoundException()
        return CommunityResponse.from_model(community)

    async def list(
        self,
        user_id: uuid.UUID,
        db_sess: AsyncSession,
        *,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[CommunityResponse], bool]:
        result = await db_sess.execute(
            select(Community)
            .where(Community.user_id == user_id)
            .order_by(Community.id.desc())
            .offset((page - 1) * limit)
            .limit(limit + 1)
        )
        communities = list(result.scalars().all())
        has_next = len(communities) > limit
        return [
            CommunityResponse.from_model(community)
            for community in communities[:limit]
        ], has_next

    async def update(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID,
        request: CommunityUpdate,
        db_sess: AsyncSession,
    ) -> CommunityResponse:
        community = await db_sess.scalar(
            select(Community).where(
                Community.id == id,
                Community.user_id == user_id,
            )
        )
        if community is None:
            raise CommunityNotFoundException()

        if request.policy is not None:
            community.policy = request.policy

        await db_sess.flush()
        await db_sess.refresh(community)
        return CommunityResponse.from_model(community)

    async def delete(
        self, id: uuid.UUID, user_id: uuid.UUID, db_sess: AsyncSession
    ) -> None:
        community = await db_sess.scalar(
            select(Community).where(
                Community.id == id,
                Community.user_id == user_id,
            )
        )
        if community is None:
            raise CommunityNotFoundException()

        if await self._moderator_service.has_active_in_community(id, db_sess):
            raise CommunityHasActiveModeratorsException()

        await db_sess.delete(community)
