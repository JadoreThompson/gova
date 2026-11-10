import logging
import uuid
from datetime import timedelta

import discord

from lib.util import get_datetime
from moderator.action.discord import (
    DiscordAction,
    DiscordReplyAction,
    DiscordTimeoutAction,
    DiscordActionType,
)
from moderator.agent import evaluate_message
from moderator.conversation.discord import MinifiedDiscordMessage
from moderator.conversation.manager import ConversationManager


class DiscordModerator:
    def __init__(
        self,
        conversation_manager: ConversationManager,
        guild_id: int,
        policy: str,
        require_approval: bool = True,
        batch_window: int = 60,
    ):
        """
        Args:
            conversation_manager (ConversationManager): _description_
            guild_id (int): _description_
            policy (str): _description_
            batch_window (int, optional): In seconds, the time window for batching messages. Defaults to 60.
        """
        self._id = uuid.uuid4()
        self._guild_id = guild_id
        self._conversation_manager = conversation_manager
        self._policy = policy
        self._require_approval = require_approval
        self._batch_window = batch_window
        self._logger = logging.getLogger(f"{self.__class__.__name__}::{self._id}")

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def guild_id(self) -> int:
        return self._guild_id

    def set_policy(self, policy: str):
        self._policy = policy

    def get_policy(self) -> str:
        return self._policy

    def set_require_approval(self, require_approval: bool):
        self._require_approval = require_approval

    def get_require_approval(self) -> bool:
        return self._require_approval

    async def on_message(self, message: discord.Message):
        if message.guild.id != self._guild_id:
            raise ValueError(
                f"Message {message.id} from guild {message.guild.id} is not from the configured guild {self._guild_id}"
            )

        messages = [
            MinifiedDiscordMessage.from_discord_message(msg)
            for msg in await self._get_message_conversation(message)
        ]

        evaluation = await evaluate_message(
            MinifiedDiscordMessage.from_discord_message(message),
            messages,
            self._policy,
        )
        print(
            f"Evaluation for message {message.id} by user {message.author.id}: {evaluation}"
        )

        if evaluation.action is not None:
            await self.execute_action(evaluation.action, message)

    async def _get_message_conversation(
        self, message: discord.Message
    ) -> list[discord.Message]:
        max_messages = 200
        recent_limit = 100
        buffer: dict[int, discord.Message] = {}

        def add(candidate: discord.Message) -> bool:
            if candidate.id == message.id or candidate.id in buffer:
                return False
            if len(buffer) >= max_messages:
                return False
            buffer[candidate.id] = candidate
            return True

        async def resolve_parent(
            current: discord.Message,
        ) -> discord.Message | None:
            reference = current.reference
            if reference is None or reference.message_id is None:
                return None

            resolved = reference.resolved
            if isinstance(resolved, discord.Message):
                return resolved

            channel = current.channel
            if reference.channel_id is not None and reference.channel_id != channel.id:
                channel = current.guild.get_channel(reference.channel_id) or channel

            try:
                return await channel.fetch_message(reference.message_id)
            except discord.HTTPException:
                return None

        async def walk_reply_chain(start: discord.Message) -> None:
            current = start
            while len(buffer) < max_messages:
                parent = await resolve_parent(current)
                if parent is None or not add(parent):
                    break
                current = parent

        await walk_reply_chain(message)

        if len(buffer) < max_messages:
            async for recent in message.channel.history(limit=recent_limit):
                if len(buffer) >= max_messages:
                    break
                add(recent)
                await walk_reply_chain(recent)

        return sorted(buffer.values(), key=lambda msg: msg.created_at)

    async def execute_action(self, action: DiscordAction, message: discord.Message):
        if self._require_approval:
            self._logger.info(f"Approval required for message {message.id}: {action}")
            return

        if action.type == DiscordActionType.REPLY:
            _action: DiscordReplyAction = action  # type: ignore
            await message.reply(_action.content)
        elif action.type == DiscordActionType.TIMEOUT:
            _action: DiscordTimeoutAction = action  # type: ignore
            await message.author.timeout(
                get_datetime() + timedelta(seconds=_action.duration)
            )
        elif action.type == DiscordActionType.KICK:
            await message.guild.kick(message.author)
        else:
            raise ValueError(f"Unknown action type: {action.type}")
