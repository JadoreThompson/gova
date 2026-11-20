import uuid

from pydantic import BaseModel


class RegisterModeratorRequest(BaseModel):
    moderator_id: uuid.UUID
