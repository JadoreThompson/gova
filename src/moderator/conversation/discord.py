import uuid

import discord
from pydantic import BaseModel


class MinifiedDiscordMessage(BaseModel):
    id: int
    user_id: int
    content: str
    reply_to: int | None = None

    @classmethod
    def from_discord_message(cls, message: discord.Message) -> "MinifiedDiscordMessage":
        return cls(
            id=message.id,
            user_id=message.author.id,
            content=message.content,
            reply_to=message.reference.message_id if message.reference else None,
        )


class DiscordConversation(BaseModel):
    id: uuid.UUID
    channel_id: int
    summary: str
    messages: list[MinifiedDiscordMessage]
