import asyncio
import logging

import twitchio

from community.enums import CommunityPlatform
from core.db.session import get_db_session
from event.publisher import AIOKafkaEventPublisher
from moderator.pipeline.base import IngestionPipeline
from moderator.registry import ModeratorRegistry
from moderator.service.assignment import ModeratorWorkerAssignmentService
from moderator.service.manager import ModeratorManagerService


class TwitchClient(twitchio.Client):
    """
    TwitchIO client that manages the bot's user token on startup.

    The app token generated from the client credentials is not enough to read
    or moderate chat; a user access token for the bot account is required. When
    a token and refresh token are provided they are added to the client so
    TwitchIO can validate and refresh them. Otherwise the client falls back to
    tokens previously persisted by TwitchIO (``.tio.tokens.json``).
    """

    def __init__(
        self,
        *args,
        token: str | None = None,
        refresh: str | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._user_token = token
        self._refresh_token = refresh

    async def setup_hook(self) -> None:
        if self._user_token and self._refresh_token:
            await self.add_token(self._user_token, self._refresh_token)
        elif not self.tokens:
            raise RuntimeError(
                "A Twitch user access token is required to read chat. Set "
                "TWITCH_BOT_TOKEN and TWITCH_BOT_REFRESH_TOKEN (and "
                "TWITCH_BOT_ID) or persist tokens with TwitchIO."
            )


class TwitchIngestionPipeline(IngestionPipeline):

    def __init__(
        self,
        client: twitchio.Client,
        moderator_manager_service: ModeratorManagerService,
        moderator_worker_assignment_service: ModeratorWorkerAssignmentService,
        registry: ModeratorRegistry,
        event_publisher: AIOKafkaEventPublisher,
        bot_id: str | None = None,
        worker_id: str | None = None,
        sync_interval: int = 10,
    ) -> None:
        self._client = client
        self._moderator_manager_service = moderator_manager_service
        self._moderator_worker_assignment_service = moderator_worker_assignment_service
        self._registry = registry
        self._event_publisher = event_publisher
        self._bot_id = bot_id
        self._worker_id = worker_id
        self._sync_interval = sync_interval
        self._platform = CommunityPlatform.TWITCH
        self._subscribed_channels: set[str] = set()
        self._logger = logging.getLogger(self.__class__.__name__)

    def set_worker_id(self, worker_id: str):
        if self._worker_id:
            raise ValueError("Cannot reassign value for worker id")
        self._worker_id = worker_id

    async def run(self):
        self._ensure_worker_id()
        self._assign_events()
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._client.start(with_adapter=False))
            tg.create_task(self._sync_loop())

    @property
    def platform(self):
        return self._platform

    @property
    def client(self) -> twitchio.Client:
        return self._client

    @property
    def subscribed_channels(self) -> set[str]:
        return set(self._subscribed_channels)

    def _assign_events(self):

        @self._client.listen("ready")
        async def on_ready() -> None:
            self._logger.info("Twitch client is ready")

        @self._client.listen("message")
        async def on_message(message: twitchio.ChatMessage) -> None:
            """
            Retrieve moderator from registry and let it process the message.
            """
            try:
                moderator = self._registry.get_by_community(
                    self._platform, message.broadcaster.id
                )
            except ValueError:
                self._logger.warning(
                    "Received a Twitch message for unregistered channel '%s'",
                    message.broadcaster.id,
                )
                return

            await moderator.process_message(message)

    async def _sync_loop(self):
        await self._client.wait_until_ready()

        while True:
            try:
                await self._sync_moderators()
            except Exception:
                self._logger.exception("Failed to sync Twitch moderators")
            await asyncio.sleep(self._sync_interval)

    async def _sync_moderators(self):
        """Create missing moderators from assignments and subscribe to channels."""
        await self._load_assignments()
        await self._subscribe_channels()

    async def _load_assignments(self):
        async with get_db_session() as db_sess:
            try:
                assignments = (
                    await self._moderator_worker_assignment_service.list_by_worker(
                        self._worker_id, db_sess
                    )
                )
                for assignment in assignments:
                    try:
                        await self._moderator_manager_service.create(
                            assignment.moderator_id, self._worker_id, db_sess
                        )
                    except Exception:
                        self._logger.exception(
                            "Failed to create Twitch moderator '%s'",
                            assignment.moderator_id,
                        )
                await db_sess.commit()
            except Exception:
                await db_sess.rollback()
                raise

    async def _subscribe_channels(self):
        for moderator in list(self._registry):
            if moderator.platform != self._platform:
                continue
            if moderator.community_id in self._subscribed_channels:
                continue

            try:
                await self._subscribe(moderator.community_id)
            except Exception:
                self._logger.exception(
                    "Failed to subscribe to Twitch channel '%s'",
                    moderator.community_id,
                )

    async def _subscribe(self, channel_id: str):
        if not self._bot_id:
            raise ValueError("Twitch bot id is not set")

        payload = twitchio.eventsub.ChatMessageSubscription(
            broadcaster_user_id=channel_id,
            user_id=self._bot_id,
        )
        await self._client.subscribe_websocket(payload, as_bot=True)
        self._subscribed_channels.add(channel_id)
        self._logger.info("Subscribed to Twitch chat for channel '%s'", channel_id)

    def _ensure_worker_id(self):
        if not self._worker_id:
            raise ValueError("Worker id is not set")
