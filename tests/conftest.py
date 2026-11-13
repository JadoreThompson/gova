import os
import uuid
from typing import Callable

from event.kafka import AIOKafkaProducerFactory
from event.publisher import AIOKafkaEventPublisher

os.environ.setdefault("JWT_COOKIE_ALIAS", "test-cookie")
os.environ.setdefault("JWT_ALGO", "HS256")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("JWT_EXPIRY_SECS", "3600")

import pytest
import pytest_asyncio
from argon2 import PasswordHasher
from testcontainers.kafka import KafkaContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from auth.service import AuthService
from community.service import CommunityService
from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    POSTGRES_DB,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USERNAME,
    REDIS_PORT,
)
from core.db.client import POSTGRES_ENGINE_SYNC
from core.db.model import Base
from core.db.session import get_db_session_sync
from security.jwt.service import JWTService
from moderator.service import ModeratorService
from tests.perf.flags import PERF_ENV_VAR, perf_enabled, real_llm_enabled
from user.service import UserService

# config.py reads these at import time. When the LLM is stubbed, dummy values
# keep imports working without a .env. Real-LLM mode falls through to .env so
# the actual provider credentials are used.
if not real_llm_enabled():
    os.environ.setdefault("DISCORD_BOT_TOKEN", "test-token")
    os.environ.setdefault("LLM_API_KEY", "test-key")
    os.environ.setdefault("LLM_BASE_URL", "http://127.0.0.1:9")


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "perf: opt-in performance tests, enabled with GOVA_PERF_TESTS=1",
    )


def pytest_collection_modifyitems(config, items):
    if perf_enabled():
        return

    skip = pytest.mark.skip(
        reason=f"performance tests are opt-in; set {PERF_ENV_VAR}=1 to run"
    )
    for item in items:
        if "perf" in item.keywords:
            item.add_marker(skip)


# ===================
## Data Layer
# ===================


@pytest.fixture(scope="session", autouse=True)
def postgres_container():
    with PostgresContainer(
        "postgres:18",
        username=POSTGRES_USERNAME,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB,
    ).with_bind_ports(5432, POSTGRES_PORT) as postgres:
        yield postgres


@pytest.fixture(scope="session", autouse=True)
def kafka_container():
    port = int(KAFKA_BOOTSTRAP_SERVERS.split(":")[1])
    with KafkaContainer().with_kraft().with_bind_ports(9093, port) as kafka:
        yield kafka


@pytest.fixture(scope="session", autouse=True)
def redis_container():
    with RedisContainer("redis:8").with_bind_ports(6379, REDIS_PORT) as redis:
        yield redis


@pytest.fixture(scope="session", autouse=True)
def setup(postgres_container):
    from sqlalchemy import text

    with POSTGRES_ENGINE_SYNC.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        Base.metadata.create_all(bind=conn)

    yield


# ===================
## Services
# ===================


@pytest_asyncio.fixture(loop_scope="session")
async def kafka_event_publisher():
    return AIOKafkaEventPublisher(AIOKafkaProducerFactory.create())


@pytest.fixture
def moderator_service(kafka_event_publisher):
    return ModeratorService(kafka_event_publisher)


@pytest.fixture
def community_service(moderator_service):
    return CommunityService(moderator_service=moderator_service)


@pytest.fixture
def password_hasher():
    return PasswordHasher()


@pytest.fixture
def user_service(password_hasher):
    return UserService(password_hasher)


@pytest.fixture
def jwt_service():
    return JWTService(
        jwt_secret="test-secret-that-is-at-least-32-bytes-long",
        jwt_algo="HS256",
        jwt_expiry_secs=3600,
        cookie_alias="test-cookie",
        is_production=False,
    )


@pytest.fixture
def auth_service(user_service, jwt_service):
    return AuthService(user_service=user_service, jwt_service=jwt_service)


# =============
# Helpers
# =============


@pytest.fixture
def create_user() -> Callable[..., uuid.UUID]:
    """Creates a user and returns it's id"""

    def _func(
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ) -> uuid.UUID:
        import uuid
        from user.model import User

        suffix = uuid.uuid4().hex
        username = username or f"community-owner-{suffix}"
        email = email or f"community-owner-{suffix}@example.com"
        password = password or "password-1"

        with get_db_session_sync() as db_sess:
            user = User(username=username, email=email, password=password)
            db_sess.add(user)
            db_sess.commit()
            return user.id

    return _func
