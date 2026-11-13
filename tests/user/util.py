import uuid
from unittest.mock import AsyncMock, Mock

from user.model import User
from user.schema import UserCreate
from user.service import UserService


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


def make_user(**overrides):
    suffix = uuid.uuid4().hex
    values = {
        "username": f"user-{suffix}",
        "email": f"user-{suffix}@example.com",
        "password": "password-1",
    }
    values.update(overrides)
    return User(**values)


def make_create(**overrides):
    suffix = uuid.uuid4().hex
    values = {
        "username": f"user-{suffix}",
        "email": f"user-{suffix}@example.com",
        "password": "password-1",
    }
    values.update(overrides)
    return UserCreate(**values)


def make_service():
    return UserService()
