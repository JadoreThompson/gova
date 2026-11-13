import uuid

from pydantic import BaseModel, Field


class JWTPayload(BaseModel):
    sub: uuid.UUID
    em: str
    exp: int
    jti: uuid.UUID = Field(default_factory=uuid.uuid4)
