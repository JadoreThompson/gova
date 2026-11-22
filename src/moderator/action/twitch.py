from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TwitchActionType(str, Enum):
    REPLY = "reply"
    TIMEOUT = "timeout"
    BAN = "ban"


class TwitchReplyAction(BaseModel):
    type: Literal[TwitchActionType.REPLY] = Field(
        TwitchActionType.REPLY, frozen=True
    )
    content: str = Field(
        ..., description="The public reply to post in the channel chat."
    )
    reply_to: str = Field(..., description="The id of the target message to reply to.")


class TwitchTimeoutAction(BaseModel):
    type: Literal[TwitchActionType.TIMEOUT] = Field(
        TwitchActionType.TIMEOUT, frozen=True
    )
    user_id: str = Field(
        ..., description="The id of the target message author to timeout."
    )
    duration: int = Field(
        ..., description="Timeout duration in seconds (1 to 1209600)."
    )
    reason: str | None = Field(
        default=None, description="Optional reason for the timeout."
    )


class TwitchBanAction(BaseModel):
    type: Literal[TwitchActionType.BAN] = Field(TwitchActionType.BAN, frozen=True)
    user_id: str = Field(..., description="The id of the target message author to ban.")
    reason: str | None = Field(default=None, description="Optional reason for the ban.")


TwitchAction = Annotated[
    TwitchReplyAction | TwitchTimeoutAction | TwitchBanAction,
    Field(discriminator="type"),
]
