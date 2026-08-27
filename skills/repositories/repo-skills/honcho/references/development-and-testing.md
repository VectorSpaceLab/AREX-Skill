# Development and testing

This file is for maintenance workflows: checks, tests, type validation, release
coordination, and script usage.

## Main checks

From the repository root:

- `uv run pytest tests/`
- `uv run pytest tests/ -k typescript`
- `uv run python -m tests.unified.run`
- `uv run python -m tests.unified.run --test-dir tests/unified/test_cases`
- `uv run ruff check src/`
- `uv run ruff format src/`
- `uv run basedpyright`
- `cd sdks/typescript && bun run tsc --noEmit`

## Test surface map

- `tests/routes/` — API route policy, scopes, CRUD, and response behavior.
- `tests/sdk/` — Python SDK integration and surface checks.
- `tests/sdk_typescript/` — TypeScript SDK checks driven through pytest.
- `tests/llm/` — model config, request builder, registry, and tool-loop tests.
- `tests/startup/` — embedding and startup validation.
- `tests/scripts/` — repo script behavior.
- `tests/vector_store/` — vector-store behavior and namespace probing.
- `tests/bench/` and `tests/live_llm/` — heavier or gated suites.

## Script inventory that matters for maintenance

A maintainer should know the intent of these repo scripts:

- `scripts/configure_embeddings.py` — embedding-dimension configuration and
  inventory reporting.
- `scripts/generate_jwt.py` — scoped JWT generation.
- `scripts/run_alembic_tests.py` — selective Alembic test selection.
- `scripts/ensure_alembic_tests.py` — validation helper for Alembic tests.
- `scripts/update_version.py` — coordinated version bump helper.
- `scripts/provision_db.py` / `scripts/migrate_db.py` — operational database
  setup helpers.
- `scripts/test_reasoning_levels.py` — reasoning-level test helper.

## Development cautions

- Do not run `bun test` directly for the TypeScript SDK. The supported path is
  the pytest-driven monorepo test command.
- Do not write to a read-only DB session.
- Do not hold a DB session open across external calls.
- Do not use `allow_member_read=True` on mutating routes.
- Do not treat live provider suites as a substitute for local unit coverage.

## Release hygiene

A coordinated release usually needs the API, Python SDK, and TypeScript SDK to
stay version-aligned. The version bump helper exists for that reason, but the
underlying source of truth remains the package metadata in each project file.

## When to read this file

Read this file when the user asks about adding or running tests, debugging a
failing check, verifying a repo change, or preparing a release-adjacent update.
