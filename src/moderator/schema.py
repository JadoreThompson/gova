from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from moderator.enums import ModeratorPlatform, ModeratorStatus
from moderator.model import (
    ModeratorWorker,
    ModeratorWorkerAssignment,
    Moderator,
)


class ModeratorCreate(BaseModel):
    platform: ModeratorPlatform
    platform_community_id: str = Field(min_length=1)
    community_policy: Annotated[
        str,
        StringConstraints(min_length=1, strip_whitespace=True),
    ] = Field(..., min_length=3)
    name: str = Field(min_length=1)
    action_config: dict[str, dict] = Field(default_factory=dict)


class ModeratorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    action_config: dict[str, dict] | None = None


class ModeratorPolicyUpdate(BaseModel):
    community_policy: Annotated[
        str,
        StringConstraints(min_length=1, strip_whitespace=True),
    ] = Field(..., min_length=3)


class ModeratorResponse(BaseModel):
    id: uuid.UUID
    platform: ModeratorPlatform
    platform_community_id: str
    community_policy: str
    name: str
    action_config: dict[str, dict]
    status: ModeratorStatus
    created_at: datetime

    @classmethod
    def from_model(cls, moderator: Moderator) -> "ModeratorResponse":
        return cls(
            id=moderator.id,
            platform=moderator.platform,
            platform_community_id=moderator.platform_community_id,
            community_policy=moderator.community_policy,
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
    platform: ModeratorPlatform = ModeratorPlatform.DISCORD


class ModeratorWorkerResponse(BaseModel):
    id: str
    platform: ModeratorPlatform
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
