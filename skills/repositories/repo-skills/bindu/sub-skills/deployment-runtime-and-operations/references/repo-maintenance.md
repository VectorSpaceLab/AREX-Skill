# Repo Maintenance

Use `uv sync` after dependency changes. Fast feedback: `uv run pytest tests/unit/`. Full validation can include `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run mypy bindu`, and `uv run pre-commit run --all-files`.

TypeScript SDK: `cd sdks/typescript && npm run build`.

Proto changes: edit `proto/agent_handler.proto`, then run `bash scripts/generate_protos.sh all`. Do not edit generated stubs directly.

Coding rules: use `get_logger(__name__)`, use `app_settings`, prefer `dict.pop(key, None)` for optional keys, and never commit `.env` files.
