import uuid
from unittest.mock import AsyncMock

from moderator.enums import ModeratorPlatform
from moderator.service.manager import ModeratorManagerService
from moderator.service.worker import ModeratorWorkerService
from moderator.worker.worker import ModeratorWorker


def make_worker(
    *,
    id: str | None = None,
    capacity: int = 10,
    host: str = "127.0.0.1",
    port: int = 9100,
    platform: ModeratorPlatform = ModeratorPlatform.DISCORD,
    moderator_worker_service: ModeratorWorkerService | None = None,
    moderator_manager_service: ModeratorManagerService | None = None,
    heartbeat_interval: int = 0,
) -> ModeratorWorker:
    return ModeratorWorker(
        id=id or f"worker-{uuid.uuid4().hex}",
        capacity=capacity,
        host=host,
        port=port,
        platform=platform,
        moderator_worker_service=moderator_worker_service
        or AsyncMock(spec=ModeratorWorkerService),
        moderator_manager_service=moderator_manager_service
        or AsyncMock(spec=ModeratorManagerService),
        pipeline=AsyncMock(),
        heartbeat_interval=heartbeat_interval,
    )
