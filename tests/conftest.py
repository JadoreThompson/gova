import os

import pytest

from tests.perf.flags import PERF_ENV_VAR, perf_enabled, real_llm_enabled

# config.py reads these at import time. When the LLM is stubbed, dummy values
# keep imports working without a .env. Real-LLM mode falls through to .env so
# the actual provider credentials are used.
if not real_llm_enabled():
    os.environ.setdefault("DISCORD_BOT_TOKEN", "test-token")
    os.environ.setdefault("LLM_API_KEY", "test-key")
    os.environ.setdefault("LLM_BASE_URL", "http://127.0.0.1:9")


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "perf: opt-in performance tests, enabled with GOVA_PERF_TESTS=1",
    )


def pytest_collection_modifyitems(config, items):
    if perf_enabled():
        return

    skip = pytest.mark.skip(
        reason=f"performance tests are opt-in; set {PERF_ENV_VAR}=1 to run"
    )
    for item in items:
        if "perf" in item.keywords:
            item.add_marker(skip)
