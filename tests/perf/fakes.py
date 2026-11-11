"""Lightweight stand-ins for the discord.py objects used by DiscordModerator.

These fakes let the real ``DiscordModerator.on_message`` pipeline run without a
Discord connection or a live LLM. Only the attributes and methods the pipeline
actually touches are implemented.
"""

from __future__ import annotations

import asyncio
import io
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

import discord

from moderator.agent import EvaluationAgentOutput
from moderator.conversation.manager import ConversationManager
from moderator.discord import DiscordModerator

from . import corpus
from .flags import real_llm_enabled

POLICY = (
    "Be respectful to other members. Harassment, hate speech, threats, doxxing, "
    "and spam or scam content are not allowed."
)


class FakeHTTPException(discord.HTTPException):
    def __init__(self) -> None:
        Exception.__init__(self, "fake message not found")


class FakeAuthor:
    def __init__(self, user_id: int) -> None:
        self.id = user_id
        self.timeouts: list[object] = []

    async def timeout(self, until) -> None:
        self.timeouts.append(until)


class FakeGuild:
    def __init__(self, guild_id: int) -> None:
        self.id = guild_id
        self._channels: dict[int, "FakeChannel"] = {}
        self.kicks: list[int] = []

    def add_channel(self, channel: "FakeChannel") -> None:
        self._channels[channel.id] = channel

    def get_channel(self, channel_id: int) -> "FakeChannel | None":
        return self._channels.get(channel_id)

    async def kick(self, author: FakeAuthor) -> None:
        self.kicks.append(author.id)


class FakeReference:
    def __init__(self, message_id: int, channel_id: int) -> None:
        self.message_id = message_id
        self.channel_id = channel_id
        self.resolved = None


class FakeChannel:
    def __init__(self, channel_id: int) -> None:
        self.id = channel_id
        self._messages: dict[int, "FakeMessage"] = {}

    def add(self, message: "FakeMessage") -> None:
        self._messages[message.id] = message

    async def history(self, limit: int = 100):
        ordered = sorted(
            self._messages.values(),
            key=lambda message: message.created_at,
            reverse=True,
        )
        for message in ordered[:limit]:
            yield message

    async def fetch_message(self, message_id: int) -> "FakeMessage":
        try:
            return self._messages[message_id]
        except KeyError:
            raise FakeHTTPException() from None


class FakeMessage:
    def __init__(
        self,
        *,
        id: int,
        author: FakeAuthor,
        content: str,
        created_at,
        channel: FakeChannel,
        guild: FakeGuild,
        reference: FakeReference | None = None,
    ) -> None:
        self.id = id
        self.author = author
        self.content = content
        self.created_at = created_at
        self.channel = channel
        self.guild = guild
        self.reference = reference
        self.replies: list[str] = []

    async def reply(self, content: str) -> None:
        self.replies.append(content)


@dataclass
class FakeDay:
    guild: FakeGuild
    channel: FakeChannel
    messages: list[FakeMessage]


def build_day(day_index: int) -> FakeDay:
    guild = FakeGuild(corpus.GUILD_ID)
    channel = FakeChannel(corpus.CHANNEL_ID + day_index)
    guild.add_channel(channel)

    authors: dict[int, FakeAuthor] = {}
    messages: list[FakeMessage] = []
    for spec in corpus.messages_for_day(day_index):
        author = authors.get(spec.user_id)
        if author is None:
            author = FakeAuthor(spec.user_id)
            authors[spec.user_id] = author
        reference = (
            FakeReference(spec.reply_to, channel.id)
            if spec.reply_to is not None
            else None
        )
        messages.append(
            FakeMessage(
                id=spec.id,
                author=author,
                content=spec.content,
                created_at=spec.created_at,
                channel=channel,
                guild=guild,
                reference=reference,
            )
        )

    for message in messages:
        channel.add(message)

    return FakeDay(guild=guild, channel=channel, messages=messages)


def make_moderator(*, require_approval: bool = True) -> DiscordModerator:
    return DiscordModerator(
        conversation_manager=ConversationManager(),
        guild_id=corpus.GUILD_ID,
        policy=POLICY,
        event_publisher=AsyncMock(),
        require_approval=require_approval,
    )


BENIGN_EVALUATION = EvaluationAgentOutput(
    score=0.0,
    reason="Benign test message.",
    action=None,
)


@contextmanager
def suppress_pipeline_output():
    """Discard the per-message prints the pipeline emits during a perf run."""

    with redirect_stdout(io.StringIO()):
        yield


@contextmanager
def evaluator_harness(*, latency_ms: float = 0.0):
    """Stub the LLM call unless ``GOVA_PERF_REAL_LLM`` is set.

    In real-LLM mode nothing is patched and ``latency_ms`` is ignored, so the
    measured numbers include the provider's actual latency and behaviour.
    """

    if real_llm_enabled():
        yield
        return

    async def _evaluate(message, conversation_messages, policy):
        if latency_ms > 0:
            await asyncio.sleep(latency_ms / 1000.0)
        return BENIGN_EVALUATION

    with patch("moderator.discord.evaluate_message", new=_evaluate):
        yield
