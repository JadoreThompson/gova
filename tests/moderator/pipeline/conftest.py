from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from moderator.pipeline.discord import DiscordIngestionPipeline


class FakeDiscordClient:
    """Minimal client that registers event handlers like discord.Client."""

    def __init__(self) -> None:
        self.handlers = {}
        self.start = AsyncMock()

    def event(self, func):
        self.handlers[func.__name__] = func
        setattr(self, func.__name__, func)
        return func


@asynccontextmanager
async def _db_session(db_sess):
    yield db_sess


@pytest.fixture
def discord_client():
    return FakeDiscordClient()


@pytest.fixture
def moderator_manager_service():
    service = MagicMock()
    service.create_discord = AsyncMock()
    service.destroy = AsyncMock()
    return service


@pytest.fixture
def registry():
    return MagicMock()


@pytest.fixture
def db_session(monkeypatch):
    db_sess = MagicMock(commit=AsyncMock())
    monkeypatch.setattr(
        "moderator.pipeline.discord.get_db_session",
        lambda: _db_session(db_sess),
    )
    return db_sess


def _build_pipeline(client, moderator_manager_service, registry, worker_id):
    return DiscordIngestionPipeline(
        client=client,
        community_service=MagicMock(),
        moderator_service=MagicMock(),
        moderator_worker_assignment_service=MagicMock(),
        moderator_manager_service=moderator_manager_service,
        registry=registry,
        event_publisher=MagicMock(),
        worker_id=worker_id,
    )


@pytest_asyncio.fixture(loop_scope="session")
async def pipeline(discord_client, moderator_manager_service, registry):
    pipeline = _build_pipeline(
        discord_client, moderator_manager_service, registry, "test-worker"
    )
    await pipeline.run()
    return pipeline


@pytest_asyncio.fixture(loop_scope="session")
async def pipeline_without_worker_id(discord_client, moderator_manager_service, registry):
    pipeline = _build_pipeline(
        discord_client, moderator_manager_service, registry, None
    )
    await pipeline.run()
    return pipeline
