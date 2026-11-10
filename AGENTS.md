# AGENTS.md

AI-powered Discord community moderator. Python 3.13, `uv`, `pydantic-ai` v2, `discord.py` 2.x.

## Commands

- `uv sync` — install deps from `uv.lock`. Add deps with `uv add <pkg>` (never hand-edit `uv.lock`).
- `uv run python src/main.py` — intended bot entrypoint (see env gotcha below).
- `uv run pytest` — runs the test suite. Performance tests are opt-in: `$env:GOVA_PERF_TESTS=1; uv run pytest tests/perf -s` (PowerShell) or `GOVA_PERF_TESTS=1 uv run pytest tests/perf -s` (bash). Add `GOVA_PERF_REAL_LLM=1` to call the configured provider instead of the stub (capped by `GOVA_PERF_REAL_LLM_MAX_MESSAGES`, default 60).
- No linter, typechecker, CI, or pre-commit are configured. Don't invent commands.

## Layout

- `src/` is the import root. Imports are absolute from it (`from moderator.agent import ...`, `from config import ...`); do not add a `src.` prefix or relative imports.
- `src/main.py` — discord.py client wiring. `src/config.py` — env loading and LLM settings.
- `src/moderator/agent.py` — pydantic-ai `Agent`, `SYSTEM_PROMPT`, `EvaluationAgentOutput`, `evaluate_message()`.
- `src/moderator/discord.py` — `DiscordModerator`: receives messages, calls the agent, executes actions.
- `src/moderator/action/discord.py` — `DiscordAction` union (reply/timeout/kick) + `DiscordActionType`.
- `src/moderator/conversation/` — `MinifiedDiscordMessage`, `DiscordConversation`, `ConversationManager`.
- `src/moderator/manager.py` + `base.py` — `ModeratorManager` over the `Moderator` ABC; not wired into the bot.

## Style

- Pydantic `BaseModel` for all DTOs and LLM structured output; `async` for anything touching Discord or the LLM.
- Moderation policy lives in the agent prompt/`policy` argument; the model judges only the target message, using prior messages as context.
