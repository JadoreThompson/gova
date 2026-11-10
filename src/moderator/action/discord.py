from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class DiscordActionType(str, Enum):
    REPLY = "reply"
    KICK = "kick"
    TIMEOUT = "timeout"


class DiscordReplyAction(BaseModel):
    type: Literal["reply"]
    content: str = Field(..., description="The public reply to post under the target message.")
    reply_to: int = Field(..., description="The id of the target message to reply to.")


class DiscordKickAction(BaseModel):
    type: Literal["kick"]
    user_id: int = Field(..., description="The id of the target message author to kick.")


class DiscordTimeoutAction(BaseModel):
    type: Literal["timeout"]
    user_id: int = Field(..., description="The id of the target message author to timeout.")
    duration: int = Field(
        ..., description="Timeout duration in seconds (60 to 604800)."
    )  # Duration in seconds


DiscordAction = Annotated[
    DiscordReplyAction | DiscordKickAction | DiscordTimeoutAction,
    Field(discriminator="type"),
]
