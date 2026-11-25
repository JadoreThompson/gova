import httpx
import pytest

from auth.exception import TwitchOAuthException
from auth.service.twitch import TwitchOAuthService


def _make_service(handler) -> TwitchOAuthService:
    return TwitchOAuthService(
        client_id="test-client-id",
        client_secret="test-client-secret",
        redirect_uri="https://example.com/auth/twitch/callback",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_exchange_code_returns_tokens():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://id.twitch.tv/oauth2/token")
        body = request.content.decode()
        assert "grant_type=authorization_code" in body
        assert "client_id=test-client-id" in body
        assert "code=test-code" in body
        return httpx.Response(
            200,
            json={
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "expires_in": 3600,
                "scope": ["chat:read"],
                "token_type": "bearer",
            },
        )

    service = _make_service(handler)

    tokens = await service.exchange_code("test-code")

    assert tokens.access_token == "access-token"
    assert tokens.refresh_token == "refresh-token"
    assert tokens.expires_in == 3600
    assert tokens.scope == ["chat:read"]
    assert tokens.token_type == "bearer"


@pytest.mark.asyncio
async def test_exchange_code_raises_for_error_response():
    service = _make_service(
        lambda request: httpx.Response(400, json={"message": "Invalid code"})
    )

    with pytest.raises(TwitchOAuthException):
        await service.exchange_code("bad-code")


@pytest.mark.asyncio
async def test_exchange_code_raises_for_invalid_payload():
    service = _make_service(lambda request: httpx.Response(200, content=b"not-json"))

    with pytest.raises(TwitchOAuthException):
        await service.exchange_code("test-code")


@pytest.mark.asyncio
async def test_exchange_code_raises_for_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    service = _make_service(handler)

    with pytest.raises(TwitchOAuthException):
        await service.exchange_code("test-code")
