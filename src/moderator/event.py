import uuid
from datetime import datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter

from lib.util import get_datetime
from moderator.action.discord import DiscordAction


class ModeratorEventType(str, Enum):
    ACTION = "action"
    STARTED = "started"
    STOPPED = "stopped"
    START = "start"
    STOP = "stop"
    PING = "ping"
    PONG = "pong"


class ModeratorEvent(BaseModel):
    moderator_id: uuid.UUID
    timestamp: datetime = Field(default_factory=get_datetime)


class ModeratorActionEvent(ModeratorEvent):
    type: Literal[ModeratorEventType.ACTION] = ModeratorEventType.ACTION
    action: DiscordAction
    message_id: int


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
    ),
    Field(discriminator="type"),
]

moderator_inbound_event_adapter = TypeAdapter(ModeratorEventUnion)


def parse_moderator_event(payload: bytes | str) -> ModeratorEventUnion:
    return moderator_inbound_event_adapter.validate_json(payload)
