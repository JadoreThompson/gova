from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from community.enums import CommunityPlatform
from moderator.enums import ModeratorStatus
from moderator.model import (
    ModeratorWorker,
    ModeratorWorkerAssignment,
    Moderator,
)


class ModeratorCreate(BaseModel):
    community_id: uuid.UUID
    name: str = Field(min_length=1)
    action_config: dict[str, dict] = Field(default_factory=dict)


class ModeratorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    action_config: dict[str, dict] | None = None


class ModeratorResponse(BaseModel):
    id: uuid.UUID
    community_id: uuid.UUID
    name: str
    action_config: dict[str, dict]
    status: ModeratorStatus
    created_at: datetime

    @classmethod
    def from_model(cls, moderator: Moderator) -> "ModeratorResponse":
        return cls(
            id=moderator.id,
            community_id=moderator.community_id,
            name=moderator.name,
            action_config=moderator.action_config,
            status=moderator.status,
            created_at=moderator.created_at,
        )


class ModeratorWorkerCreate(BaseModel):
    id: str = Field(min_length=1)
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    capacity: int = Field(ge=1)
    platform: CommunityPlatform = CommunityPlatform.DISCORD


class ModeratorWorkerResponse(BaseModel):
    id: str
    platform: CommunityPlatform
    host: str
    port: int
    count: int
    capacity: int
    last_heartbeat: int

    @classmethod
    def from_model(cls, worker: ModeratorWorker) -> "ModeratorWorkerResponse":
        return cls(
            id=worker.id,
            platform=worker.platform,
            host=worker.host,
            port=worker.port,
            count=worker.count,
            capacity=worker.capacity,
            last_heartbeat=worker.last_heartbeat,
        )


class ModeratorWorkerAssignmentResponse(BaseModel):
    id: uuid.UUID
    moderator_id: uuid.UUID
    worker_id: str

    @classmethod
    def from_model(
        cls, assignment: ModeratorWorkerAssignment
    ) -> "ModeratorWorkerAssignmentResponse":
        return cls(
            id=assignment.id,
            moderator_id=assignment.moderator_id,
            worker_id=assignment.worker_id,
        )
