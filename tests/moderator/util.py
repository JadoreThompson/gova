import uuid

from community.enums import CommunityPlatform
from community.schema import CommunityCreate
from core.db.session import get_db_session
from moderator.schema import ModeratorCreate


def make_create(community_id: uuid.UUID, **overrides) -> ModeratorCreate:
    values = {
        "community_id": community_id,
        "name": "Moderator",
        "action_config": {},
    }
    values.update(overrides)
    return ModeratorCreate(**values)


async def make_community(community_service, user_id: uuid.UUID):
    async with get_db_session() as db_sess:
        community = await community_service.create(
            CommunityCreate(
                platform=CommunityPlatform.DISCORD,
                community_id=f"community-{uuid.uuid4()}",
                policy="Be nice.",
            ),
            user_id,
            db_sess,
        )
        await db_sess.commit()
        return community
