from unittest.mock import MagicMock

import discord
import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_on_guild_join(
    pipeline, discord_client, moderator_manager_service, db_session
):
    guild = MagicMock(spec=discord.Guild)
    guild.id = 123

    await discord_client.on_guild_join(guild)

    moderator_manager_service.create_discord.assert_awaited_once_with(
        123, "test-worker", db_session
    )
    db_session.commit.assert_awaited_once()


@pytest.mark.asyncio(loop_scope="session")
async def test_on_guild_join_raises_when_worker_id_not_set(
    pipeline_without_worker_id, discord_client, moderator_manager_service, monkeypatch
):
    guild = MagicMock(spec=discord.Guild)
    guild.id = 123

    get_db_session = MagicMock()
    monkeypatch.setattr("moderator.pipeline.discord.get_db_session", get_db_session)

    with pytest.raises(ValueError):
        await discord_client.on_guild_join(guild)

    get_db_session.assert_not_called()
    moderator_manager_service.create_discord.assert_not_awaited()
