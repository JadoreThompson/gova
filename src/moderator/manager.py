import uuid

from moderator.base import Moderator


class ModeratorManager:
    def __init__(self):
        self._moderators: dict[uuid.UUID, Moderator] = {}

    def add_moderator(self, moderator: Moderator) -> None:
        self._moderators[moderator.id] = moderator

    def get_moderator(self, moderator_id: uuid.UUID) -> Moderator:
        if moderator_id in self._moderators:
            return self._moderators[moderator_id]
        raise ValueError(f"Moderator with ID {moderator_id} not found.")

    def remove_moderator(self, moderator_id: uuid.UUID) -> None:
        self.get_moderator(moderator_id)
        del self._moderators[moderator_id]
