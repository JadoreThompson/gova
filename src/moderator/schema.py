from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from moderator.enums import ModeratorStatus
from moderator.model import Moderators


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
    def from_model(cls, moderator: Moderators) -> "ModeratorResponse":
        return cls(
            id=moderator.id,
            community_id=moderator.community_id,
            name=moderator.name,
            action_config=moderator.action_config,
            status=moderator.status,
            created_at=moderator.created_at,
        )
