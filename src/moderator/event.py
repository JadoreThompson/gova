import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter, model_validator

from moderator.enums import ModeratorPlatform
from lib.util import get_datetime
from moderator.action.discord import DiscordAction
from moderator.action.twitch import TwitchAction
discord_action_adapter = TypeAdapter(DiscordAction)
twitch_action_adapter = TypeAdapter(TwitchAction)


class ModeratorEventType(str, Enum):
    ACTION = "action"
    STARTED = "started"
    STOPPED = "stopped"
    START = "start"
    STOP = "stop"
    PING = "ping"
    PONG = "pong"
    POLICY_UPDATED = "policy_updated"


class ModeratorEvent(BaseModel):
    moderator_id: uuid.UUID
    timestamp: datetime = Field(default_factory=get_datetime)


class ModeratorActionEvent(ModeratorEvent):
    type: Literal[ModeratorEventType.ACTION] = ModeratorEventType.ACTION
    platform: ModeratorPlatform = ModeratorPlatform.DISCORD
    action: Any
    message_id: int | str

    @model_validator(mode="after")
    def _validate_action(self) -> "ModeratorActionEvent":
        if self.platform == ModeratorPlatform.TWITCH:
            self.action = twitch_action_adapter.validate_python(self.action)
        else:
            self.action = discord_action_adapter.validate_python(self.action)
        return self


class ModeratorStartEvent(ModeratorEvent):
    type: Literal[ModeratorEventType.START] = ModeratorEventType.START


class ModeratorStartedEvent(ModeratorEvent):
    type: Literal[ModeratorEventType.STARTED] = ModeratorEventType.STARTED


class ModeratorStopEvent(ModeratorEvent):
    type: Literal[ModeratorEventType.STOP] = ModeratorEventType.STOP


class ModeratorStoppedEvent(ModeratorEvent):
    type: Literal[ModeratorEventType.STOPPED] = ModeratorEventType.STOPPED


class ModeratorPingEvent(ModeratorEvent):
    type: Literal[ModeratorEventType.PING] = ModeratorEventType.PING


class ModeratorPongEvent(ModeratorEvent):
    type: Literal[ModeratorEventType.PONG] = ModeratorEventType.PONG


class ModeratorPolicyUpdatedEvent(ModeratorEvent):
    type: Literal[ModeratorEventType.POLICY_UPDATED] = (
        ModeratorEventType.POLICY_UPDATED
    )


ModeratorInboundEvent = Annotated[
    ModeratorStartEvent | ModeratorStopEvent | ModeratorPingEvent | ModeratorPongEvent,
    Field(discriminator="type"),
]

ModeratorEventUnion = Annotated[
    (
        ModeratorActionEvent
        | ModeratorStartEvent
        | ModeratorStartedEvent
        | ModeratorStopEvent
        | ModeratorStoppedEvent
        | ModeratorPingEvent
        | ModeratorPongEvent
        | ModeratorPolicyUpdatedEvent
    ),
    Field(discriminator="type"),
]

moderator_inbound_event_adapter = TypeAdapter(ModeratorEventUnion)


def parse_moderator_event(payload: bytes | str) -> ModeratorEventUnion:
    return moderator_inbound_event_adapter.validate_json(payload)
