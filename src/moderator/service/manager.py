import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from community.enums import CommunityPlatform
from community.schema import CommunityResponse
from community.service import CommunityService
from config import KAFKA_MODERATOR_EVENTS_TOPIC
from event.publisher import EventPublisher
from moderator.base import BaseModeratorService
from moderator.conversation.manager import ConversationManager
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
        community_service: CommunityService,
        moderator_worker_assignment_service: ModeratorWorkerAssignmentService,
        registry: ModeratorRegistry,
        event_publisher: EventPublisher,
        twitch_bot_id: str | None = None,
    ) -> None:
        self._moderator_service = moderator_service
        self._community_service = community_service
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
        community = await self._community_service.get_by_id(
            moderator.community_id, db_sess
        )

        mod = self._create_moderator(community, moderator)
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
        community = await self._community_service.get_by_community(
            str(guild_id), CommunityPlatform.DISCORD, db_sess
        )
        moderator = await self._moderator_service.get_by_community(
            community.id, db_sess
        )
        mod = self._create_discord_moderator(community, moderator)
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
        self, community: CommunityResponse, moderator: ModeratorResponse
    ) -> BaseModeratorService:
        if community.platform == CommunityPlatform.DISCORD:
            return self._create_discord_moderator(community, moderator)
        if community.platform == CommunityPlatform.TWITCH:
            return self._create_twitch_moderator(community, moderator)
        raise ValueError(f"Unsupported platform: {community.platform}")

    def _create_discord_moderator(
        self, community: CommunityResponse, moderator: ModeratorResponse
    ) -> DiscordModeratorService:
        return DiscordModeratorService(
            id=moderator.id,
            conversation_manager=ConversationManager(),
            guild_id=int(community.community_id),
            policy=community.policy,
            event_publisher=self._event_publisher,
        )

    def _create_twitch_moderator(
        self, community: CommunityResponse, moderator: ModeratorResponse
    ) -> TwitchModeratorService:
        return TwitchModeratorService(
            id=moderator.id,
            channel_id=community.community_id,
            policy=community.policy,
            event_publisher=self._event_publisher,
            bot_id=self._twitch_bot_id,
        )

    async def destroy(
        self, platform: CommunityPlatform, community_id: str, db_sess: AsyncSession
    ) -> None:
        moderator = self._registry.get_by_community(platform, community_id)
        self._registry.remove(moderator.id)
        await self._moderator_worker_assignment_service.release(moderator.id, db_sess)
