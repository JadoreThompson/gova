import uuid

from community.enums import CommunityPlatform
from moderator.base import BaseModeratorService


class ModeratorRegistry:
    def __init__(self):
        self._moderators: dict[uuid.UUID, BaseModeratorService] = {}
        self._community_2_moderator: dict[
            tuple[CommunityPlatform, str], BaseModeratorService
        ] = {}

    def add(self, moderator: BaseModeratorService) -> None:
        self._moderators[moderator.id] = moderator
        self._community_2_moderator[(moderator.platform, moderator.community_id)] = (
            moderator
        )

    def get(self, moderator_id: uuid.UUID) -> BaseModeratorService:
        if moderator_id in self._moderators:
            return self._moderators[moderator_id]
        raise ValueError(f"Moderator with ID {moderator_id} not found.")

    def get_by_community(
        self, platform: CommunityPlatform, community_id: str
    ) -> BaseModeratorService:
        key = (platform, community_id)
        if key in self._community_2_moderator:
            return self._community_2_moderator[key]
        raise ValueError(f"Moderator with community ID {community_id} not found.")

    def remove(self, moderator_id: uuid.UUID) -> None:
        mod = self.get(moderator_id)
        del self._moderators[moderator_id]
        del self._community_2_moderator[(mod.platform, mod.community_id)]

    def __contains__(self, moderator_id: uuid.UUID) -> bool:
        return moderator_id in self._moderators

    def __iter__(self):
        return iter(self._moderators.values())
