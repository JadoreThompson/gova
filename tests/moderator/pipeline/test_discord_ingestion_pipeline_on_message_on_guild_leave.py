from unittest.mock import MagicMock

import discord
import pytest

from community.enums import CommunityPlatform


@pytest.mark.asyncio(loop_scope="session")
async def test_on_guild_leave(
    pipeline, discord_client, moderator_manager_service, db_session
):
    guild = MagicMock(spec=discord.Guild)
    guild.id = 123

    await discord_client.on_guild_leave(guild)

    moderator_manager_service.destroy.assert_awaited_once_with(
        CommunityPlatform.DISCORD, "123", db_session
    )
    db_session.commit.assert_awaited_once()
