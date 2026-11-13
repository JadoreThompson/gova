from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from community.enums import CommunityPlatform
from community.model import Community


class CommunityCreate(BaseModel):
    platform: CommunityPlatform
    community_id: str = Field(min_length=1)
    policy: Annotated[
        str,
        StringConstraints(min_length=1, strip_whitespace=True),
    ] = Field(..., min_length=3)


class CommunityUpdate(BaseModel):
    policy: Annotated[
        str | None,
        StringConstraints(min_length=1, strip_whitespace=True),
    ] = Field(default=None, min_length=3)


class CommunityResponse(BaseModel):
    id: uuid.UUID
    platform: CommunityPlatform
    community_id: str
    policy: str

    @classmethod
    def from_model(cls, community: Community) -> "CommunityResponse":
        return cls(
            id=community.id,
            platform=community.platform,
            community_id=community.community_id,
            policy=community.policy,
        )
