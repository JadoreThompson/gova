import asyncio
import logging
import uuid
from collections import deque

import twitchio

from moderator.enums import ModeratorPlatform
from config import KAFKA_MODERATOR_ACTIONS_TOPIC
from core.db.session import get_db_session
from event.publisher import EventPublisher
from moderator.action.setting import ActionSettings
from moderator.action.twitch import (
    TwitchAction,
    TwitchActionType,
    TwitchBanAction,
    TwitchReplyAction,
    TwitchTimeoutAction,
)
from moderator.agent import evaluate_message
from moderator.base import BaseModeratorService
from moderator.conversation.twitch import MinifiedTwitchMessage
from moderator.event import ModeratorActionEvent

TWITCH_TIMEOUT_MAX_SECONDS = 1209600


class TwitchModeratorService(BaseModeratorService):
    def __init__(
        self,
        id: uuid.UUID,
        channel_id: str,
        policy: str,
        event_publisher: EventPublisher,
        bot_id: str | None,
        batch_window: int = 60,
        action_configs: dict[TwitchActionType, ActionSettings] | None = None,
        history_limit: int = 200,
    ):
        """
        Args:
            id (uuid.UUID): The moderator record id.
            channel_id (str): The Twitch broadcaster user id of the channel.
            policy (str): The community policy to evaluate messages against.
            event_publisher (EventPublisher): Publisher used for audit events.
            bot_id (str | None): The Twitch user id used to perform moderation actions.
            batch_window (int, optional): In seconds, the time window for batching messages. Defaults to 60.
            action_configs (dict, optional): Per-action approval settings.
            history_limit (int, optional): The number of recent messages kept for context.
        """
        self._id = id
        self._channel_id = channel_id
        self._policy = policy
        self._event_publisher = event_publisher
        self._bot_id = bot_id
        self._batch_window = batch_window
        self._action_configs = action_configs or {}
        self._history: deque[MinifiedTwitchMessage] = deque(maxlen=history_limit)
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(f"{self.__class__.__name__}::{self._id}")

    @property
    def id(self) -> uuid.UUID:
        return self._id

    @property
    def platform_community_id(self) -> str:
        return self._channel_id

    @property
    def platform(self):
        return ModeratorPlatform.TWITCH

    def set_policy(self, policy: str):
        self._policy = policy

    def get_policy(self) -> str:
        return self._policy

    async def process_message(self, message: twitchio.ChatMessage):
        if self._bot_id and message.chatter.id == self._bot_id:
            return

        async with self._lock:
            if message.broadcaster.id != self._channel_id:
                raise ValueError(
                    f"Message {message.id} from channel {message.broadcaster.id} is not from the configured channel {self._channel_id}"
                )

            messages = list(self._history)
            target = MinifiedTwitchMessage.from_twitch_message(message)
            self._history.append(target)

        evaluation = await evaluate_message(
            target,
            messages,
            self._policy,
            platform=self.platform,
        )

        if evaluation.action is not None:
            await self.execute_action(evaluation.action, message)

    async def execute_action(
        self, action: TwitchAction, message: twitchio.ChatMessage
    ) -> None:
        event = ModeratorActionEvent(
            moderator_id=self._id,
            platform=self.platform,
            action=action,
            message_id=message.id,
        )
        async with get_db_session() as db_sess:
            await self._event_publisher.publish(
                event, KAFKA_MODERATOR_ACTIONS_TOPIC, db_sess
            )

        if self._action_configs and (
            action.type not in self._action_configs
            or self._action_configs[action.type].requires_approval
        ):
            self._logger.warning(
                f"Lack permission for action type {action.type} for message {message.id}"
            )
            return

        if action.type == TwitchActionType.REPLY:
            _action: TwitchReplyAction = action  # type: ignore
            if self._bot_id:
                await message.respond(_action.content, token_for=self._bot_id)
            else:
                await message.respond(_action.content)
        elif action.type == TwitchActionType.TIMEOUT:
            _action: TwitchTimeoutAction = action  # type: ignore
            duration = max(1, min(_action.duration, TWITCH_TIMEOUT_MAX_SECONDS))
            await message.chatter.timeout(
                moderator=self._bot_id,
                duration=duration,
                reason=_action.reason,
            )
        elif action.type == TwitchActionType.BAN:
            _action: TwitchBanAction = action  # type: ignore
            await message.chatter.ban(
                moderator=self._bot_id,
                reason=_action.reason,
            )
        else:
            raise ValueError(f"Unknown action type: {action.type}")
