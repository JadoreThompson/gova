from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from user.model import User
from user.schema import UserResponse


class LoginRequest(BaseModel):
    email: Annotated[
        str,
        StringConstraints(min_length=1, strip_whitespace=True),
    ] = Field(..., min_length=3)
    password: Annotated[
        str,
        StringConstraints(min_length=1),
    ] = Field(..., min_length=3)


UserLogin = LoginRequest


class LoginResponse(BaseModel):
    jwt_token: str
    user: UserResponse

    @classmethod
    def from_model(cls, user: User, jwt_token: str) -> "LoginResponse":
        return cls(jwt_token=jwt_token, user=UserResponse.from_model(user))
