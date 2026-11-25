import logging
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from community.enums import CommunityPlatform
from config import TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_REDIRECT_URI
from ..exception import TwitchOAuthException
from ..model import PlatformToken
from ..schema import PlatformTokenResponse, TwitchTokenResponse

TWITCH_TOKEN_URL = "https://id.twitch.tv/oauth2/token"


class TwitchOAuthService:
    def __init__(
        self,
        client_id: str = TWITCH_CLIENT_ID,
        client_secret: str = TWITCH_CLIENT_SECRET,
        redirect_uri: str = TWITCH_REDIRECT_URI,
        token_url: str = TWITCH_TOKEN_URL,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._token_url = token_url
        self._transport = transport
        self._logger = logging.getLogger(self.__class__.__name__)

    async def exchange_code(self, code: str) -> TwitchTokenResponse:
        """Exchange a Twitch authorization code for an access token."""
        payload = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self._redirect_uri,
        }

        try:
            async with httpx.AsyncClient(
                timeout=10.0, transport=self._transport
            ) as client:
                rsp = await client.post(self._token_url, data=payload)
                # rsp.raise_for_status()
                body = rsp.json()
                print(f"response body: {body}")
                if rsp.status_code != 200:
                    raise httpx.HTTPError("")
                return TwitchTokenResponse.model_validate(rsp.json())
        except (httpx.HTTPError, ValueError) as e:
            self._logger.warning("Twitch token exchange failed: %s", e)
            raise TwitchOAuthException() from e

    async def connect(
        self, user_id: uuid.UUID, code: str, db_sess: AsyncSession
    ) -> PlatformTokenResponse:
        """Link a user's Twitch account by storing the exchanged tokens."""
        tokens = await self.exchange_code(code)
        print(f"twitch oauth tokens: {tokens}")

        platform_token = await db_sess.scalar(
            select(PlatformToken).where(
                PlatformToken.user_id == user_id,
                PlatformToken.platform == CommunityPlatform.TWITCH,
            )
        )

        if platform_token is None:
            platform_token = PlatformToken(
                user_id=user_id,
                platform=CommunityPlatform.TWITCH,
                token=tokens.access_token,
                refresh_token=tokens.refresh_token,
            )
            db_sess.add(platform_token)
        else:
            platform_token.token = tokens.access_token
            platform_token.refresh_token = tokens.refresh_token

        await db_sess.flush()
        await db_sess.refresh(platform_token)
        return PlatformTokenResponse.from_model(platform_token)
