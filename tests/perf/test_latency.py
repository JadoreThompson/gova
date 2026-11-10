"""Percentile latency tests for the Discord moderation pipeline.

The whole ``DiscordModerator.on_message`` flow runs against the hard-coded
three-day corpus. By default the LLM call is stubbed with zero added latency so
the numbers reflect the bot's own per-message overhead (context assembly,
minification, evaluation hand-off, action dispatch).

Set ``GOVA_PERF_REAL_LLM=1`` to call the configured provider instead. In that
mode the sample is capped by ``GOVA_PERF_REAL_LLM_MAX_MESSAGES`` (default 60)
to bound API usage and runtime.

Opt in with ``GOVA_PERF_TESTS=1``.
"""

from __future__ import annotations

import asyncio
import os
import time

import pytest

from . import corpus
from .fakes import (
    build_day,
    evaluator_harness,
    make_moderator,
    suppress_pipeline_output,
)
from .flags import real_llm_enabled, real_llm_max_messages
from .metrics import format_percentiles, latency_percentiles

_DEFAULT_BUDGET_MS = "1000" if real_llm_enabled() else "250"
LATENCY_BUDGET_MS = float(
    os.environ.get("GOVA_PERF_LATENCY_BUDGET_MS", _DEFAULT_BUDGET_MS)
)


def _target_messages() -> list[corpus.MockMessage]:
    if real_llm_enabled():
        return corpus.sample_messages(real_llm_max_messages())
    return list(corpus.MOCK_MESSAGES)


async def _collect_latencies_ms(targets: list[corpus.MockMessage]) -> list[float]:
    moderator = make_moderator(require_approval=True)
    target_ids = {message.id for message in targets}
    latencies_ms: list[float] = []

    with evaluator_harness(latency_ms=0.0), suppress_pipeline_output():
        for day_index in range(corpus.DAY_COUNT):
            day = build_day(day_index)
            for message in day.messages:
                if message.id not in target_ids:
                    continue
                started = time.perf_counter()
                await moderator.on_message(message)
                latencies_ms.append((time.perf_counter() - started) * 1000.0)

    return latencies_ms


@pytest.mark.perf
def test_percentile_latency():
    targets = _target_messages()
    latencies_ms = asyncio.run(_collect_latencies_ms(targets))
    percentiles = latency_percentiles(latencies_ms)
    mean_ms = sum(latencies_ms) / len(latencies_ms)
    mode = "real-llm" if real_llm_enabled() else "stubbed-llm"

    print(
        f"\nlatency ({mode}) over {len(latencies_ms)} messages: "
        f"mean={mean_ms:.2f}ms, {format_percentiles(percentiles)}"
    )
