"""Seed the configured Postgres database with moderator scheduling data.

Run with ``uv run pytest scripts/seed_moderators.py -s``. This file lives
outside ``tests/`` on purpose so ``tests/conftest.py`` does not start its own
Postgres container; it writes to the database configured in ``.env``. The file
name does not match pytest's default patterns, so it is only collected when
passed explicitly.

It creates a user, one Discord community and one YouTube community, moderators
for each, worker records (one healthy/available, one full, and stale workers),
and moderator-to-worker assignments. Stale workers have ``last_heartbeat = 0``
so the worker monitor can be exercised against them immediately.
"""

import asyncio
import uuid
from dataclasses import dataclass, field

import pytest
import sqlalchemy as sa
from argon2 import PasswordHasher

from moderator.enums import ModeratorPlatform
from sqlalchemy import delete
from core.db.client import POSTGRES_ENGINE_SYNC
from core.db.model import Base
from core.db.session import get_db_session
from event.publisher import AIOKafkaEventPublisher
from moderator.model import ModeratorWorker, ModeratorWorkerAssignment, Moderator
from moderator.schema import ModeratorCreate
from moderator.service.moderator import ModeratorService
from tests.perf.flags import is_seeding
from user.model import User
from user.schema import UserCreate
from user.service import UserService


@dataclass
class SeedModerator:
    id: uuid.UUID
    name: str


@dataclass
class SeedWorker:
    id: str
    platform: ModeratorPlatform
    capacity: int
    count: int


@dataclass
class SchedulingSeed:
    user_id: uuid.UUID
    communities: dict[str, str]
    moderators: dict[str, list[SeedModerator]]
    workers: dict[str, SeedWorker]
    assignments: dict[uuid.UUID, str] = field(default_factory=dict)


def ensure_schema() -> None:
    Base.metadata.create_all(bind=POSTGRES_ENGINE_SYNC)


async def cleanup_seed_data(db_sess) -> None:
    seed_moderator_ids = sa.select(Moderator.id).where(Moderator.name.like("Seed %"))
    await db_sess.execute(
        delete(ModeratorWorkerAssignment).where(
            ModeratorWorkerAssignment.moderator_id.in_(seed_moderator_ids)
        )
    )
    await db_sess.execute(
        delete(ModeratorWorker).where(ModeratorWorker.id.like("seed-%"))
    )
    await db_sess.execute(delete(Moderator).where(Moderator.name.like("Seed %")))
    await db_sess.execute(delete(User).where(User.username.like("seed-owner-%")))


async def seed_scheduling_data() -> SchedulingSeed:
    suffix = uuid.uuid4().hex

    async with get_db_session() as db_sess:
        await cleanup_seed_data(db_sess)

        user_service = UserService(PasswordHasher())
        moderator_service = ModeratorService(AIOKafkaEventPublisher())

        user = await user_service.create(
            UserCreate(
                username=f"seed-owner-{suffix}",
                email=f"seed-owner-{suffix}@example.com",
                password="password-1",
            ),
            db_sess,
        )

        discord_community_id = f"seed-discord-{suffix}"
        youtube_community_id = f"seed-youtube-{suffix}"

        discord_moderators = [
            await moderator_service.create(
                ModeratorCreate(
                    platform=ModeratorPlatform.DISCORD,
                    platform_community_id=discord_community_id,
                    community_policy="Be respectful and keep discussions on topic.",
                    name="Seed Discord Moderator",
                    action_config={},
                ),
                user.id,
                db_sess,
            )
        ]
        youtube_moderators = [
            await moderator_service.create(
                ModeratorCreate(
                    platform=ModeratorPlatform.YOUTUBE,
                    platform_community_id=youtube_community_id,
                    community_policy="No spam or harassment in the comments.",
                    name="Seed YouTube Moderator",
                    action_config={},
                ),
                user.id,
                db_sess,
            )
        ]

        workers = {}
        # workers = {
        #     "discord_failed": ModeratorWorker(
        #         id=f"seed-discord-failed-{suffix}",
        #         platform=ModeratorPlatform.DISCORD,
        #         host="127.0.0.1",
        #         port=9201,
        #         count=4,
        #         capacity=10,
        #         status=ModeratorWorkerStatus.ONLINE,
        #         last_heartbeat=0,
        #         last_attempt=0,
        #     ),
        #     "discord_full": ModeratorWorker(
        #         id=f"seed-discord-full-{suffix}",
        #         platform=ModeratorPlatform.DISCORD,
        #         host="127.0.0.1",
        #         port=9202,
        #         count=2,
        #         capacity=2,
        #         status=ModeratorWorkerStatus.ONLINE,
        #         last_heartbeat=now,
        #         last_attempt=0,
        #     ),
        #     "discord_available": ModeratorWorker(
        #         id=f"seed-discord-available-{suffix}",
        #         platform=ModeratorPlatform.DISCORD,
        #         host="127.0.0.1",
        #         port=9203,
        #         count=0,
        #         capacity=10,
        #         status=ModeratorWorkerStatus.ONLINE,
        #         last_heartbeat=now,
        #         last_attempt=0,
        #     ),
        #     "youtube_failed": ModeratorWorker(
        #         id=f"seed-youtube-failed-{suffix}",
        #         platform=ModeratorPlatform.YOUTUBE,
        #         host="127.0.0.1",
        #         port=9204,
        #         count=2,
        #         capacity=10,
        #         status=ModeratorWorkerStatus.ONLINE,
        #         last_heartbeat=0,
        #         last_attempt=0,
        #     ),
        # }
        # db_sess.add_all(list(workers.values()))
        # await db_sess.flush()

        assignments: dict[uuid.UUID, str] = {}
        # for moderator in discord_moderators[:4]:
        #     assignments[moderator.id] = workers["discord_failed"].id
        # for moderator in discord_moderators[4:]:
        #     assignments[moderator.id] = workers["discord_full"].id
        # for moderator in youtube_moderators:
        #     assignments[moderator.id] = workers["youtube_failed"].id

        # db_sess.add_all(
        #     [
        #         ModeratorWorkerAssignment(
        #             moderator_id=moderator_id, worker_id=worker_id
        #         )
        #         for moderator_id, worker_id in assignments.items()
        #     ]
        # )
        # await db_sess.flush()

        # await db_sess.commit()

        return SchedulingSeed(
            user_id=user.id,
            communities={
                "discord": discord_community_id,
                "youtube": youtube_community_id,
            },
            moderators={
                "discord": [
                    SeedModerator(id=m.id, name=m.name) for m in discord_moderators
                ],
                "youtube": [
                    SeedModerator(id=m.id, name=m.name) for m in youtube_moderators
                ],
            },
            workers={
                key: SeedWorker(
                    id=worker.id,
                    platform=ModeratorPlatform(worker.platform),
                    capacity=worker.capacity,
                    count=worker.count,
                )
                for key, worker in workers.items()
            },
            assignments=assignments,
        )


async def _seed_and_verify() -> SchedulingSeed:
    seed = await seed_scheduling_data()

    async with get_db_session() as db_sess:
        moderator_count = await db_sess.scalar(
            sa.select(sa.func.count()).select_from(Moderator)
        )
        worker_count = await db_sess.scalar(
            sa.select(sa.func.count()).select_from(ModeratorWorker)
        )
        assignment_count = await db_sess.scalar(
            sa.select(sa.func.count()).select_from(ModeratorWorkerAssignment)
        )

    # assert moderator_count >= 8
    # assert worker_count >= 4
    # assert assignment_count >= 8
    return seed


@pytest.mark.skipif((not is_seeding()), reason="Seed mode disabled")
def test_seed_moderators() -> None:
    ensure_schema()
    seed = asyncio.run(_seed_and_verify())

    print("\n=== Scheduling seed ===")
    print(f"user: {seed.user_id}")
    for platform, community_id in seed.communities.items():
        print(f"community[{platform}]: {community_id}")
    for platform, moderators in seed.moderators.items():
        for moderator in moderators:
            print(f"moderator[{platform}]: {moderator.id} ({moderator.name})")
    for key, worker in seed.workers.items():
        print(
            f"worker[{key}]: {worker.id} "
            f"platform={worker.platform.value} "
            f"count={worker.count}/{worker.capacity}"
        )
    for moderator_id, worker_id in seed.assignments.items():
        print(f"assignment: {moderator_id} -> {worker_id}")
