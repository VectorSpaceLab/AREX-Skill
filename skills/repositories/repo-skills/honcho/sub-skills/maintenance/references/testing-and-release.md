# Testing and release

## Common test commands

- `uv run pytest tests/`
- `uv run pytest tests/ -k typescript`
- `uv run python -m tests.unified.run`
- `uv run python -m tests.unified.run --test-dir tests/unified/test_cases`
- `uv run ruff check src/`
- `uv run ruff format src/`
- `uv run basedpyright`
- `cd sdks/typescript && bun run tsc --noEmit`

## Useful test families

- `tests/routes/` — route policy, scopes, and CRUD checks.
- `tests/sdk/` — Python SDK integration coverage.
- `tests/sdk_typescript/` — TypeScript SDK coverage driven through pytest.
- `tests/llm/` — model config, registry, request builder, tool loop, and
  telemetry.
- `tests/startup/` — startup and embedding validation.
- `tests/scripts/` — repo script behavior.
- `tests/vector_store/` — vector-store and namespace behavior.
- `tests/live_llm/` — provider-backed suites that require credentials.
- `tests/bench/` — performance and benchmark suites.

## Release coordination

Honcho keeps three version surfaces aligned:

- the API package,
- the Python SDK,
- the TypeScript SDK.

When a release is involved, check all three package manifests together and keep
changelogs aligned with the version bump.

## Script inventory worth knowing

- `scripts/configure_embeddings.py` — embedding-dimension configuration helper.
- `scripts/generate_jwt.py` — scoped token generation.
- `scripts/run_alembic_tests.py` — selective Alembic test routing.
- `scripts/update_version.py` — coordinated version bump helper.
- `scripts/ensure_alembic_tests.py` — Alembic test validation helper.
- `scripts/provision_db.py` and `scripts/migrate_db.py` — operational helpers.

## Maintenance heuristics

- Prefer a targeted test first.
- Escalate to a broader suite only if the affected surface crosses boundaries.
- Treat live-provider suites as optional unless the task explicitly needs them.
- Keep static checks in the loop for schema, route, or package metadata changes.
- Use the selector helper when you are not sure which tests are relevant.
