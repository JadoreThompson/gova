"""Throughput tests for the Discord moderation pipeline.

Each rate ``n`` (messages per minute) is turned into the volume a two-hour
conversation would carry on every corpus day: ``n * 120`` messages per day.
The harness feeds that offered load through the real ``on_message`` pipeline
with bounded concurrency and asserts the sustained processing rate is at least
``n`` messages per minute.

By default the LLM call is stubbed. Set ``GOVA_PERF_MODEL_LATENCY_MS`` to the
model's observed latency to make the capacity estimate reflect production.
Set ``GOVA_PERF_REAL_LLM=1`` to call the configured provider instead; that mode
caps the offered load at ``GOVA_PERF_REAL_LLM_MAX_MESSAGES`` (default 60) to
bound API usage and runtime.

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


def _rates() -> list[float]:
    raw = os.environ.get("GOVA_PERF_THROUGHPUT_RATES", "1,5,10")
    rates = [float(part) for part in raw.split(",") if part.strip()]
    if not rates:
        raise ValueError("GOVA_PERF_THROUGHPUT_RATES must list at least one rate")
    return rates


RATES = _rates()
CONCURRENCY = int(os.environ.get("GOVA_PERF_CONCURRENCY", "8"))
MODEL_LATENCY_MS = float(os.environ.get("GOVA_PERF_MODEL_LATENCY_MS", "5"))


def _offered_messages(rate: float):
    per_day = max(1, round(rate * corpus.CONVERSATION_MINUTES))
    if real_llm_enabled():
        per_day = min(per_day, max(1, real_llm_max_messages() // corpus.DAY_COUNT))

    offered = []
    for day_index in range(corpus.DAY_COUNT):
        day = build_day(day_index)
        for index in range(per_day):
            offered.append(day.messages[index % len(day.messages)])
    return offered


async def _run(rate: float):
    moderator = make_moderator(require_approval=True)
    semaphore = asyncio.Semaphore(CONCURRENCY)
    offered = _offered_messages(rate)
    completed = 0

    async def handle(message):
        nonlocal completed
        async with semaphore:
            await moderator.on_message(message)
            completed += 1

    with evaluator_harness(latency_ms=MODEL_LATENCY_MS), suppress_pipeline_output():
        started = time.perf_counter()
        await asyncio.gather(*(handle(message) for message in offered))
        elapsed = time.perf_counter() - started

    return len(offered), completed, elapsed


@pytest.mark.perf
@pytest.mark.parametrize("rate", RATES, ids=lambda rate: f"{rate:g}_msg_per_min")
def test_throughput(rate):
    offered, completed, elapsed = asyncio.run(_run(rate))
    achieved_per_minute = completed / elapsed * 60.0
    per_day_seconds = elapsed / corpus.DAY_COUNT
    daily_budget_seconds = corpus.CONVERSATION_MINUTES * 60
    mode = (
        "real-llm"
        if real_llm_enabled()
        else f"stubbed-llm(latency={MODEL_LATENCY_MS:g}ms)"
    )

    print(
        f"\nrate={rate:g} msg/min [{mode}]: offered={offered}, completed={completed}, "
        f"elapsed={elapsed:.3f}s, achieved={achieved_per_minute:.1f} msg/min "
        f"(concurrency={CONCURRENCY})"
    )

    assert completed == offered
    assert achieved_per_minute >= rate
    assert per_day_seconds <= daily_budget_seconds
