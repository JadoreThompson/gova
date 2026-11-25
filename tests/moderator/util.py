import uuid

from core.db.session import get_db_session
from moderator.enums import ModeratorPlatform
from moderator.schema import ModeratorCreate


def make_create(**overrides) -> ModeratorCreate:
    values = {
        "platform": ModeratorPlatform.DISCORD,
        "platform_community_id": f"community-{uuid.uuid4()}",
        "community_policy": "Be nice.",
        "name": "Moderator",
        "action_config": {},
    }
    values.update(overrides)
    return ModeratorCreate(**values)


async def make_moderator(moderator_service, user_id: uuid.UUID, **overrides):
    async with get_db_session() as db_sess:
        moderator = await moderator_service.create(
            make_create(**overrides), user_id, db_sess
        )
        await db_sess.commit()
        return moderator
