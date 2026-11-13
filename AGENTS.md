# AGENTS.md

AI-powered Discord community moderator with a FastAPI backend in progress. Python 3.13, `uv`, pydantic-ai v2, discord.py 2.x, FastAPI, async SQLAlchemy over Postgres, Redis, Kafka.

## Commands

- `uv run pytest` — full suite. Single file/test: `uv run pytest tests/user/test_user_create.py -q`.
- Perf tests are opt-in: `$env:GOVA_PERF_TESTS=1; uv run pytest tests/perf -s` (PowerShell) or `GOVA_PERF_TESTS=1 uv run pytest tests/perf -s` (bash). `GOVA_PERF_REAL_LLM=1` calls the real provider instead of the stub, capped by `GOVA_PERF_REAL_LLM_MAX_MESSAGES` (default 60). See `README.md` for the other `GOVA_PERF_*` flags.
- No linter, typechecker, CI, or pre-commit are configured. Don't invent commands.

## Testing quirks

- Integration tests start real Postgres/Kafka/Redis via `testcontainers` — Docker must be running. Containers bind the ports from `.env`, so don't run the suite alongside `docker-compose.yaml`.
- DB tests use `@pytest.mark.asyncio(loop_scope="session")`; keep that scope or the shared engine/session breaks. Copy the pattern from `tests/community/test_community_create.py`.
- Tests target services against the real DB (fixtures in `conftest.py`), not HTTP routers.

## Layout

- Domain packages (`auth`, `user`, `community`, `moderator`) share one shape: `model.py` (SQLAlchemy), `schema.py` (Pydantic DTOs), `service.py`, `router.py`, `exception.py`, `enums.py`. Service methods take `db_sess: AsyncSession` as the last argument and raise domain exceptions; routers don't catch them.

## Style

- Pydantic `BaseModel` for all DTOs and LLM structured output; `async` for anything touching DB, Discord, Kafka, or the LLM.
