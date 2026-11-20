from __future__ import annotations

from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints


class LoginRequest(BaseModel):
    email: Annotated[
        str,
        StringConstraints(min_length=1, strip_whitespace=True),
    ] = Field(..., min_length=3)
    password: Annotated[
        str,
        StringConstraints(min_length=1),
    ] = Field(..., min_length=3)
