import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from config import KAFKA_MODERATOR_EVENTS_TOPIC
from event.publisher import EventPublisher
from moderator.base import BaseModeratorService
from moderator.conversation.manager import ConversationManager
from moderator.enums import ModeratorPlatform
from moderator.event import ModeratorStartedEvent
from moderator.registry import ModeratorRegistry
from moderator.schema import ModeratorResponse
from moderator.service.assignment import ModeratorWorkerAssignmentService
from moderator.service.discord import DiscordModeratorService
from moderator.service.moderator import ModeratorService
from moderator.service.twitch import TwitchModeratorService


class ModeratorManagerService:
    def __init__(
        self,
        moderator_service: ModeratorService,
        moderator_worker_assignment_service: ModeratorWorkerAssignmentService,
        registry: ModeratorRegistry,
        event_publisher: EventPublisher,
        twitch_bot_id: str | None = None,
    ) -> None:
        self._moderator_service = moderator_service
        self._moderator_worker_assignment_service = moderator_worker_assignment_service
        self._registry = registry
        self._event_publisher = event_publisher
        self._twitch_bot_id = twitch_bot_id

    async def create(
        self, moderator_id: uuid.UUID, worker_id: str, db_sess: AsyncSession
    ) -> BaseModeratorService:
        """
        Constructs the moderator instance for the given id, assigns it to the
        worker and publishes a started event.
        """
        moderator = await self._moderator_service.get_by_id(moderator_id, db_sess)

        mod = self._create_moderator(moderator)
        self._registry.add(mod)

        await self._moderator_worker_assignment_service.assign(
            moderator.id, worker_id, db_sess
        )
        await self._event_publisher.publish(
            ModeratorStartedEvent(moderator_id=moderator.id),
            KAFKA_MODERATOR_EVENTS_TOPIC,
            db_sess,
        )

        return mod

    async def create_discord(
        self, guild_id: int, worker_id: str, db_sess: AsyncSession
    ) -> DiscordModeratorService:
        """
        Creates instance, assigns instance to worker
        """
        moderator = await self._moderator_service.get_by_platform_community(
            ModeratorPlatform.DISCORD, str(guild_id), db_sess
        )
        mod = self._create_discord_moderator(moderator)
        self._registry.add(mod)

        await self._moderator_worker_assignment_service.assign(
            moderator.id, worker_id, db_sess
        )
        await self._event_publisher.publish(
            ModeratorStartedEvent(moderator_id=moderator.id),
            KAFKA_MODERATOR_EVENTS_TOPIC,
            db_sess,
        )

        return mod

    def _create_moderator(
        self, moderator: ModeratorResponse
    ) -> BaseModeratorService:
        if moderator.platform == ModeratorPlatform.DISCORD:
            return self._create_discord_moderator(moderator)
        if moderator.platform == ModeratorPlatform.TWITCH:
            return self._create_twitch_moderator(moderator)
        raise ValueError(f"Unsupported platform: {moderator.platform}")

    def _create_discord_moderator(
        self, moderator: ModeratorResponse
    ) -> DiscordModeratorService:
        return DiscordModeratorService(
            id=moderator.id,
            conversation_manager=ConversationManager(),
            guild_id=int(moderator.platform_community_id),
            policy=moderator.community_policy,
            event_publisher=self._event_publisher,
        )

    def _create_twitch_moderator(
        self, moderator: ModeratorResponse
    ) -> TwitchModeratorService:
        return TwitchModeratorService(
            id=moderator.id,
            channel_id=moderator.platform_community_id,
            policy=moderator.community_policy,
            event_publisher=self._event_publisher,
            bot_id=self._twitch_bot_id,
        )

    async def destroy(
        self,
        platform: ModeratorPlatform,
        platform_community_id: str,
        db_sess: AsyncSession,
    ) -> None:
        moderator = self._registry.get_by_platform_community(
            platform, platform_community_id
        )
        self._registry.remove(moderator.id)
        await self._moderator_worker_assignment_service.release(moderator.id, db_sess)
