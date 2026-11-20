from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from community.enums import CommunityPlatform


@pytest.mark.asyncio(loop_scope="session")
async def test_on_message_processes_message_for_guild(
    pipeline, discord_client, registry
):
    guild = MagicMock(spec=discord.Guild)
    guild.id = 123
    message = MagicMock(spec=discord.Message)
    message.guild = guild

    moderator = MagicMock()
    moderator.process_message = AsyncMock()
    registry.get_by_community.return_value = moderator

    await discord_client.on_message(message)

    registry.get_by_community.assert_called_once_with(CommunityPlatform.DISCORD, "123")
    moderator.process_message.assert_awaited_once_with(message)


@pytest.mark.asyncio(loop_scope="session")
async def test_on_message_ignores_direct_message(pipeline, discord_client, registry):
    message = MagicMock(spec=discord.Message)
    message.guild = None

    await discord_client.on_message(message)

    registry.get_by_community.assert_not_called()
