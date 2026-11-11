from enum import Enum

from pydantic import BaseModel

from moderator.action.discord import DiscordAction


class ModeratorEventType(str, Enum):
    ACTION = "action"
    STARTED = "started"
    STOPPED = "stopped"


class ModeratorActionEvent(BaseModel):
    type: ModeratorEventType = ModeratorEventType.ACTION
    action: DiscordAction
    message_id: int
