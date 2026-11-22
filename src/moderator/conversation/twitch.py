import uuid

import twitchio
from pydantic import BaseModel


class MinifiedTwitchMessage(BaseModel):
    id: str
    user_id: str
    user_name: str
    content: str
    reply_to: str | None = None

    @classmethod
    def from_twitch_message(
        cls, message: twitchio.ChatMessage
    ) -> "MinifiedTwitchMessage":
        return cls(
            id=message.id,
            user_id=message.chatter.id,
            user_name=message.chatter.name,
            content=message.text,
            reply_to=message.reply.parent_message_id if message.reply else None,
        )


class TwitchConversation(BaseModel):
    id: uuid.UUID
    channel_id: str
    summary: str
    messages: list[MinifiedTwitchMessage]
