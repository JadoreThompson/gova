import uuid
from unittest.mock import AsyncMock, Mock

from community.enums import CommunityPlatform
from community.model import Community
from community.schema import CommunityCreate
from community.service import CommunityService
from moderator.service import ModeratorService
from user.model import User  # noqa: F401  (registers the users table)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return list(self._rows)


def make_session(*, scalar=None, get=None, execute_rows=None):
    session = Mock()
    session.scalar = AsyncMock(return_value=scalar)
    session.get = AsyncMock(return_value=get)
    session.execute = AsyncMock(return_value=FakeResult(execute_rows or []))
    session.add = Mock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


def make_community(**overrides):
    values = {
        "platform": CommunityPlatform.DISCORD,
        "community_id": "community-1",
        "policy": "Be nice.",
    }
    values.update(overrides)
    return Community(**values)


def make_create(**overrides):
    values = {
        "platform": CommunityPlatform.DISCORD,
        "community_id": f"community-{uuid.uuid4()}",
        "policy": "Be nice.",
    }
    values.update(overrides)
    return CommunityCreate(**values)


def make_service(moderator_service=None):
    return CommunityService(moderator_service or AsyncMock(spec=ModeratorService))
