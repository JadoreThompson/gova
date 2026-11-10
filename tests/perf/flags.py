"""Runtime flags and knobs for the performance tests."""

from __future__ import annotations

import os
import config

PERF_ENV_VAR = "GOVA_PERF_TESTS"
REAL_LLM_ENV_VAR = "GOVA_PERF_REAL_LLM"
REAL_LLM_MAX_MESSAGES_ENV_VAR = "GOVA_PERF_REAL_LLM_MAX_MESSAGES"

_TRUTHY = {"1", "true", "yes", "on"}


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def perf_enabled() -> bool:
    return _enabled(PERF_ENV_VAR)


def real_llm_enabled() -> bool:
    # Real-LLM mode only matters when the perf suite is actually running.
    return perf_enabled() and _enabled(REAL_LLM_ENV_VAR)


def real_llm_max_messages(default: int = 60) -> int:
    raw = os.environ.get(REAL_LLM_MAX_MESSAGES_ENV_VAR, "").strip()
    if not raw:
        return default
    return max(1, int(raw))
