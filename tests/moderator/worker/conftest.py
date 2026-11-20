from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.db.session import get_db_session_dep
from moderator.service.manager import ModeratorManagerService
from moderator.service.worker import ModeratorWorkerService
from .util import make_worker


@pytest.fixture
def moderator_worker_service():
    return AsyncMock(spec=ModeratorWorkerService)


@pytest.fixture
def moderator_manager_service():
    return AsyncMock(spec=ModeratorManagerService)


@pytest.fixture
def db_sess():
    return AsyncMock()


@pytest.fixture
def worker(moderator_worker_service, moderator_manager_service):
    worker = make_worker(
        moderator_worker_service=moderator_worker_service,
        moderator_manager_service=moderator_manager_service,
    )
    worker._assign_routes()
    return worker


@pytest_asyncio.fixture(loop_scope="session")
async def client(worker, db_sess):
    worker.app.dependency_overrides[get_db_session_dep] = lambda: db_sess
    async with AsyncClient(
        transport=ASGITransport(app=worker.app), base_url="http://test"
    ) as ac:
        yield ac
