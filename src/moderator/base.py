import uuid
from abc import ABC, abstractmethod
from typing import Any

from moderator.enums import ModeratorPlatform


class BaseModeratorService(ABC):
    """
    Base class for all moderators.
    """

    @property
    @abstractmethod
    def id(self) -> uuid.UUID: ...

    @property
    @abstractmethod
    def platform(self) -> ModeratorPlatform: ...

    @property
    @abstractmethod
    def platform_community_id(self) -> str: ...

    @abstractmethod
    async def process_message(self, message: Any): ...
