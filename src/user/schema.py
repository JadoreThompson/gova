from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from user.model import User


class UserCreate(BaseModel):
    username: Annotated[
        str,
        StringConstraints(min_length=1, strip_whitespace=True),
    ] = Field(..., min_length=3)
    email: Annotated[
        str,
        StringConstraints(min_length=1, strip_whitespace=True),
    ] = Field(..., min_length=3)
    password: Annotated[
        str,
        StringConstraints(min_length=1),
    ] = Field(..., min_length=3)


class UserUpdate(BaseModel):
    username: Annotated[
        str | None,
        StringConstraints(min_length=1, strip_whitespace=True),
    ] = Field(default=None, min_length=3)


class UserPasswordUpdate(BaseModel):
    password: Annotated[
        str,
        StringConstraints(min_length=1),
    ] = Field(..., min_length=3)


class UserEmailUpdate(BaseModel):
    email: Annotated[
        str,
        StringConstraints(min_length=1, strip_whitespace=True),
    ] = Field(..., min_length=3)


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    created_at: datetime
    updated_at: datetime
    verified_at: datetime | None

    @classmethod
    def from_model(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
            verified_at=user.verified_at,
        )
