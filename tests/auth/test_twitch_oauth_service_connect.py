import httpx
import pytest
from sqlalchemy import select

from auth.model import PlatformToken
from auth.schema import PlatformTokenResponse
from auth.service.twitch import TwitchOAuthService
from community.enums import CommunityPlatform
from core.db.session import get_db_session


def _make_service(access_token: str, refresh_token: str) -> TwitchOAuthService:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": 3600,
                "scope": [],
                "token_type": "bearer",
            },
        )

    return TwitchOAuthService(
        client_id="test-client-id",
        client_secret="test-client-secret",
        redirect_uri="https://example.com/auth/twitch/callback",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_connect_stores_platform_token(create_user):
    user_id = create_user()
    service = _make_service("access-token", "refresh-token")

    async with get_db_session() as db_sess:
        result = await service.connect(user_id, "test-code", db_sess)
        await db_sess.commit()

    assert isinstance(result, PlatformTokenResponse)
    assert result.user_id == user_id
    assert result.platform == CommunityPlatform.TWITCH

    async with get_db_session() as db_sess:
        stored = await db_sess.scalar(
            select(PlatformToken).where(PlatformToken.user_id == user_id)
        )

    assert stored is not None
    assert stored.token == "access-token"
    assert stored.refresh_token == "refresh-token"
    assert stored.platform == CommunityPlatform.TWITCH


@pytest.mark.asyncio(loop_scope="session")
async def test_connect_updates_existing_platform_token(create_user):
    user_id = create_user()
    first = _make_service("first-access-token", "first-refresh-token")

    async with get_db_session() as db_sess:
        first_result = await first.connect(user_id, "first-code", db_sess)
        await db_sess.commit()

    second = _make_service("second-access-token", "second-refresh-token")
    async with get_db_session() as db_sess:
        second_result = await second.connect(user_id, "second-code", db_sess)
        await db_sess.commit()

    assert second_result.id == first_result.id

    async with get_db_session() as db_sess:
        stored = (
            await db_sess.execute(
                select(PlatformToken).where(PlatformToken.user_id == user_id)
            )
        ).scalars().all()

    assert len(stored) == 1
    assert stored[0].token == "second-access-token"
    assert stored[0].refresh_token == "second-refresh-token"
