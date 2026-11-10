from abc import ABC, abstractmethod
import uuid


class Moderator(ABC):
    """
    Base class for all moderators.
    """

    @property
    @abstractmethod
    def id(self) -> uuid.UUID: ...
