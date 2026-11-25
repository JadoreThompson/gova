from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from moderator.enums import ModeratorPlatform
from .model import PlatformToken


class LoginRequest(BaseModel):
    email: Annotated[
        str,
        StringConstraints(min_length=1, strip_whitespace=True),
    ] = Field(..., min_length=3)
    password: Annotated[
        str,
        StringConstraints(min_length=1),
    ] = Field(..., min_length=3)


class TwitchTokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_in: int | None = None
    scope: list[str] = Field(default_factory=list)
    token_type: str | None = None


class PlatformTokenResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    platform: ModeratorPlatform
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, platform_token: PlatformToken) -> "PlatformTokenResponse":
        return cls(
            id=platform_token.id,
            user_id=platform_token.user_id,
            platform=platform_token.platform,
            created_at=platform_token.created_at,
            updated_at=platform_token.updated_at,
        )
