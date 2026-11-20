import uuid
from abc import ABC, abstractmethod
from typing import Any

from community.enums import CommunityPlatform


class BaseModeratorService(ABC):
    """
    Base class for all moderators.
    """

    @property
    @abstractmethod
    def id(self) -> uuid.UUID: ...

    @property
    @abstractmethod
    def platform(self) -> CommunityPlatform: ...

    @property
    @abstractmethod
    def community_id(self) -> str: ...

    @abstractmethod
    async def process_message(self, message: Any): ...
