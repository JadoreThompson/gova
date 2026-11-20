import asyncio
import logging

import discord

from community.enums import CommunityPlatform
from config import DISCORD_BOT_TOKEN, KAFKA_MODERATOR_EVENTS_TOPIC
from community.service import CommunityService
from core.db.session import get_db_session
from event.publisher import AIOKafkaEventPublisher
from moderator.conversation.manager import ConversationManager
from moderator.service.discord import DiscordModeratorService
from moderator.enums import ModeratorStatus
from moderator.event import ModeratorStartedEvent
from moderator.pipeline.base import IngestionPipeline
from moderator.registry import ModeratorRegistry
from moderator.service.assignment import ModeratorWorkerAssignmentService
from moderator.service.manager import ModeratorManagerService
from moderator.service.moderator import ModeratorService


class DiscordIngestionPipeline(IngestionPipeline):

    def __init__(
        self,
        client: discord.Client,
        community_service: CommunityService,
        moderator_service: ModeratorService,
        moderator_worker_assignment_service: ModeratorWorkerAssignmentService,
        moderator_manager_service: ModeratorManagerService,
        registry: ModeratorRegistry,
        event_publisher: AIOKafkaEventPublisher,
        worker_id: str | None = None,
    ) -> None:
        self._client = client
        self._community_service = community_service
        self._moderator_service = moderator_service
        self._moderator_worker_assignment_service = moderator_worker_assignment_service
        self._moderator_manager_service = moderator_manager_service
        self._registry = registry
        self._event_publisher = event_publisher
        self._worker_id = worker_id
        self._platform = CommunityPlatform.DISCORD
        self._logger = logging.getLogger(self.__class__.__name__)

    def set_worker_id(self, worker_id: str):
        if self._worker_id:
            raise ValueError("Cannot reassign value for worker id")
        self._worker_id = worker_id

    async def run(self):
        self._assign_events()
        await self._client.start(DISCORD_BOT_TOKEN)

    @property
    def platform(self):
        return self._platform

    def _assign_events(self):

        @self._client.event
        async def on_ready() -> None:
            self._logger.info("Logged in as %s", self._client.user)

        @self._client.event
        async def on_guild_join(guild: discord.Guild) -> None:
            """Retrieve moderator from registry, if missing create it."""
            self._ensure_worker_id()
            async with get_db_session() as db_sess:
                await self._moderator_manager_service.create_discord(
                    guild.id, self._worker_id, db_sess
                )
                await db_sess.commit()

        @self._client.event
        async def on_guild_leave(guild: discord.Guild) -> None:
            """
            Remove moderator from registry and unassign
            """
            async with get_db_session() as db_sess:
                await self._moderator_manager_service.destroy(
                    self._platform, str(guild.id), db_sess
                )
                await db_sess.commit()

        @self._client.event
        async def on_message(message: discord.Message) -> None:
            """
            Retrieve moderator from registry, if missing create it.
            Modertor processes message
            """
            guild = message.guild
            if guild is None:
                return

            moderator = self._registry.get_by_community(self._platform, str(guild.id))
            await moderator.process_message(message)

    def _ensure_worker_id(self):
        if not self._worker_id:
            raise ValueError("Worker id is not set")
