import asyncio

import click
import discord

from community.enums import CommunityPlatform
from community.service import CommunityService
from config import (
    TWITCH_BOT_ID,
    TWITCH_BOT_REFRESH_TOKEN,
    TWITCH_BOT_TOKEN,
    TWITCH_CLIENT_ID,
    TWITCH_CLIENT_SECRET,
)
from event.publisher import AIOKafkaEventPublisher
from moderator.pipeline.discord import DiscordIngestionPipeline
from moderator.pipeline.twitch import TwitchClient, TwitchIngestionPipeline
from moderator.registry import ModeratorRegistry
from moderator.service.assignment import ModeratorWorkerAssignmentService
from moderator.service.manager import ModeratorManagerService
from moderator.service.moderator import ModeratorService
from moderator.service.worker import ModeratorWorkerService
from moderator.worker.monitor import ModeratorWorkerMonitor
from moderator.worker.worker import ModeratorWorker

PLATFORM_CHOICES = click.Choice(
    [platform.value for platform in CommunityPlatform], case_sensitive=False
)


@click.group(name="moderator")
def moderator():
    pass


@moderator.command(name="worker")
@click.option("--id", type=str, required=True)
@click.option("--capacity", type=click.IntRange(min=10), required=True)
@click.option("--host", type=str, required=True)
@click.option("--port", type=int, required=True)
@click.option(
    "--platform", type=PLATFORM_CHOICES, default=CommunityPlatform.DISCORD.value
)
@click.option("--heartbeat-interval", type=click.IntRange(min=1), default=5)
def worker(id, capacity, host, port, platform, heartbeat_interval):
    platform = CommunityPlatform(platform)
    event_publisher = AIOKafkaEventPublisher()
    moderator_service = ModeratorService(event_publisher)
    registry = ModeratorRegistry()
    community_service = CommunityService(moderator_service)
    moderator_worker_service = ModeratorWorkerService()
    moderator_worker_assignment_service = ModeratorWorkerAssignmentService(
        moderator_worker_service, moderator_service
    )
    moderator_manager_service = ModeratorManagerService(
        moderator_service=moderator_service,
        community_service=community_service,
        moderator_worker_assignment_service=moderator_worker_assignment_service,
        registry=registry,
        event_publisher=event_publisher,
        twitch_bot_id=TWITCH_BOT_ID or None,
    )

    if platform == CommunityPlatform.TWITCH:
        twitch_client = TwitchClient(
            client_id=TWITCH_CLIENT_ID,
            client_secret=TWITCH_CLIENT_SECRET or None,
            bot_id=TWITCH_BOT_ID or None,
            token=TWITCH_BOT_TOKEN or None,
            refresh=TWITCH_BOT_REFRESH_TOKEN or None,
        )
        ingestion_pipeline = TwitchIngestionPipeline(
            client=twitch_client,
            moderator_worker_assignment_service=moderator_worker_assignment_service,
            moderator_manager_service=moderator_manager_service,
            registry=registry,
            event_publisher=event_publisher,
            bot_id=TWITCH_BOT_ID or None,
        )
    elif platform == CommunityPlatform.DISCORD:
        intents = discord.Intents.default()
        intents.message_content = True
        discord_client = discord.Client(intents=intents)
        ingestion_pipeline = DiscordIngestionPipeline(
            client=discord_client,
            community_service=community_service,
            moderator_service=moderator_service,
            moderator_worker_assignment_service=moderator_worker_assignment_service,
            moderator_manager_service=moderator_manager_service,
            registry=registry,
            event_publisher=event_publisher,
        )
    else:
        raise click.ClickException(f"Unsupported platform: {platform.value}")

    worker = ModeratorWorker(
        id=id,
        capacity=capacity,
        host=host,
        port=port,
        platform=platform,
        moderator_worker_service=moderator_worker_service,
        moderator_manager_service=moderator_manager_service,
        pipeline=ingestion_pipeline,
        heartbeat_interval=heartbeat_interval,
    )

    async def _func():
        async with asyncio.TaskGroup() as tg:
            tg.create_task(worker.run())

            for _ in range(5):
                if worker.is_ready:
                    break
                await asyncio.sleep(2)

            if not worker.is_ready:
                raise Exception("Worker failed to ready")

            tg.create_task(ingestion_pipeline.run())

    asyncio.run(_func())


@moderator.command(name="monitor")
@click.option("--interval", type=click.IntRange(min=1), default=5)
@click.option("--heartbeat-timeout", type=click.IntRange(min=1), default=10)
@click.option("--last-attempt-timeout", type=click.IntRange(min=1), default=10)
@click.option(
    "--request-timeout", type=click.FloatRange(min=0, min_open=True), default=5.0
)
@click.option("--concurrency", type=click.IntRange(min=1), default=20)
def monitor(
    interval, heartbeat_timeout, last_attempt_timeout, request_timeout, concurrency
):
    event_publisher = AIOKafkaEventPublisher()
    moderator_worker_service = ModeratorWorkerService()
    moderator_service = ModeratorService(event_publisher)
    monitor = ModeratorWorkerMonitor(
        moderator_worker_service=moderator_worker_service,
        moderator_worker_assignment_service=ModeratorWorkerAssignmentService(
            moderator_worker_service, moderator_service
        ),
        heartbeat_timeout=heartbeat_timeout,
        last_attempt_timeout=last_attempt_timeout,
        interval=interval,
        request_timeout=request_timeout,
        concurrency=concurrency,
    )
    asyncio.run(monitor.run())
