import logging

import sqlalchemy as sa
from aiokafka import AIOKafkaConsumer

from community.enums import CommunityPlatform
from community.schema import CommunityResponse
from community.service import CommunityService
from config import KAFKA_MODERATOR_EVENTS_TOPIC
from core.db.session import get_db_session
from event.publisher import EventPublisher
from moderator.discord import DiscordModerator
from moderator.enums import ModeratorStatus
from moderator.event import (
    ModeratorEventType,
    ModeratorPingEvent,
    ModeratorStartEvent,
    ModeratorStartedEvent,
    ModeratorStopEvent,
    ModeratorStoppedEvent,
    parse_moderator_event,
)
from moderator.model import Moderators
from moderator.registry import ModeratorRegistry
from moderator.schema import ModeratorResponse
from moderator.service import ModeratorService
from moderator.twitch import TwitchModerator
from moderator.youtube import YouTubeModerator


class ModeratorManager:
    def __init__(
        self,
        moderator_service: ModeratorService,
        community_service: CommunityService,
        registry: ModeratorRegistry,
        kafka_consumer: AIOKafkaConsumer,
        event_publisher: EventPublisher,
    ) -> None:
        self._moderator_service = moderator_service
        self._community_service = community_service
        self._registry = registry
        self._kafka_consumer = kafka_consumer
        self._event_publisher = event_publisher
        self._logger = logging.getLogger(self.__class__.__name__)

    async def start(self):
        async for msg in self._kafka_consumer:
            event = parse_moderator_event(msg.value)

            if event.type == ModeratorEventType.START:
                await self.start_moderator(event)
            elif event.type == ModeratorEventType.STOP:
                await self.stop_moderator(event)
            elif event.type == ModeratorEventType.PING:
                await self.ping_moderator(event)

    async def start_moderator(self, event: ModeratorStartEvent):
        if event.moderator_id in self._registry:
            self._logger.info("Moderator '%s' already in register", event.moderator_id)
            return

        async with get_db_session() as db_sess:
            moderator = await self._moderator_service.get_by_id(
                event.moderator_id, db_sess, lock=True
            )
            if moderator.status != ModeratorStatus.OFFLINE:
                self._logger.warning("...")
                return

            community = await self._community_service.get_by_id(
                moderator.community_id, db_sess
            )

            if community.platform == CommunityPlatform.DISCORD:
                moderator = self._create_discord_moderator(community, moderator)
            else:
                self._logger.warning(
                    "Unsupported community platform '%s' for moderator '%s'",
                    community.platform,
                    moderator.id,
                )
                return

            await db_sess.execute(
                sa.update(Moderators)
                .where(Moderators.id == moderator.id)
                .values(status=ModeratorStatus.ONLINE)
            )

            started_event = ModeratorStartedEvent(moderator_id=moderator.id)
            await self._event_publisher.publish(
                started_event, KAFKA_MODERATOR_EVENTS_TOPIC
            )

            await db_sess.commit()

    def _create_discord_moderator(
        self, community: CommunityResponse, moderator: ModeratorResponse
    ) -> DiscordModerator: ...

    def _create_youtube_moderator(
        self, community: CommunityResponse, moderator: ModeratorResponse
    ) -> YouTubeModerator: ...

    def _create_twitch_moderator(
        self, community: CommunityResponse, moderator: ModeratorResponse
    ) -> TwitchModerator: ...

    async def stop_moderator(self, event: ModeratorStopEvent):
        moderator_id = event.moderator_id
        if moderator_id not in self._registry:
            self._logger.info("Moderator '%s' is not registered", event.moderator_id)
            return

        async with get_db_session() as db_sess:
            moderator = await self._moderator_service.get_by_id(
                moderator_id, db_sess, lock=True
            )
            if moderator.status != ModeratorStatus.ONLINE:
                self._logger.warning(
                    "Moderator '%s' with status '%s' is not online. Aborting stop request",
                    moderator_id,
                    moderator.status,
                )
                return

            self._registry.remove_moderator(moderator_id)

            await db_sess.execute(
                sa.update(Moderators)
                .where(Moderators.id == moderator_id)
                .values(status=ModeratorStatus.OFFLINE)
            )

            stopped_event = ModeratorStoppedEvent(moderator_id=moderator.id)
            await self._event_publisher.publish(
                stopped_event, KAFKA_MODERATOR_EVENTS_TOPIC
            )

            await db_sess.commit()

    async def ping_moderator(self, event: ModeratorPingEvent):
        moderator_id = event.moderator_id

        if moderator_id not in self._registry:
            self._logger.warning(
                "Moderator '%s' is not registered. Aborting ping request",
                moderator_id,
            )
            return

        ping_event = ModeratorPingEvent(moderator_id=moderator_id)
        await self._event_publisher.publish(ping_event, KAFKA_MODERATOR_EVENTS_TOPIC)
