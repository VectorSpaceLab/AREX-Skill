# Honcho Maintenance Playbook

This reference maps maintenance tasks to files, commands, and safe verification paths. It is self-contained: apply paths relative to the Honcho checkout root you are maintaining.

## Baseline Development Commands

- Install/sync: `uv sync`.
- Run server: `uv run fastapi dev src/main.py`.
- Run deriver worker: `uv run python -m src.deriver`.
- Run all ordinary tests: `uv run pytest tests/`.
- Run a single test: `uv run pytest tests/<area>/test_file.py::test_name`.
- Lint: `uv run ruff check src tests scripts migrations sdks/python`.
- Format: `uv run ruff format src tests scripts migrations sdks/python`.
- Typecheck: `uv run basedpyright`.
- Full pre-commit hooks when appropriate: `uv run pre-commit run --all-files`.

The root pytest configuration uses strict markers, xdist auto-parallelism, and ignores `tests/alembic` by default. Alembic tests need their own `-n0` path because they manage a migration pipeline.

## Change Surface Routing

### Python application code

Inspect `src/`, matching `tests/` subdirectory, `tests/conftest.py`, and the relevant router/CRUD/model/config files. Run targeted pytest first, then expand to `uv run pytest tests/` when the change can affect shared fixtures, auth, DB, queue processing, vector search, or telemetry.

### Test infrastructure

Inspect `pyproject.toml`, `.pre-commit-config.yaml`, `tests/conftest.py`, and the README in the affected test subdirectory. Preserve the collection-time live-LLM gate and the runtime-mock blocklist for tests that manage their own runtime (`tests/alembic`, `tests/bench`, `tests/unified`, `tests/live_llm`, and isolated LLM unit tests).

### TypeScript SDK

Use pytest orchestration for integration tests:

```bash
uv run pytest tests/ -k typescript
```

The TypeScript package's direct `bun test` command is intentionally a guard that fails and tells contributors to use pytest. Direct Bun use is appropriate for type/build checks only:

```bash
cd sdks/typescript && bun run typecheck
cd sdks/typescript && bun run build
```

### Auth route policy

Inspect `src/security.py`, `src/dependencies.py`, affected routers under `src/routers/`, and `tests/routes/test_auth_route_policy.py`. If a route uses `allow_member_read=True`, update the allowlist only after proving the route is read-only. For member-read routes addressing another sub-resource, add or preserve an explicit `jwt_params.p == peer_id` style check so a peer-scoped key cannot read a co-member's data.

### DB/session handling

Inspect `src/db.py`, `src/dependencies.py`, affected CRUD/router code, and tests that exercise the transaction. Keep external calls outside DB-session windows. Use read-only sessions only for SELECT-only windows; get-or-create, enqueue, vector sync state updates, cache writes, and audit-log writes are mutations even when they are hidden inside helper functions.

### LLM model config and tool loop

Inspect `src/config.py`, `src/llm/runtime.py`, `src/llm/api.py`, `src/llm/tool_loop.py`, backend adapters under `src/llm/backends/`, `src/dialectic/core.py`, `config.toml.example`, `.env.template`, and tests under `tests/llm/` plus `tests/dialectic/test_model_config_usage.py`. Preserve nested `MODEL_CONFIG` shape, fallback independence, provider-specific thinking/structured-output restrictions, AttemptPlan pinning, and `hit_input_token_cap` propagation.

Suggested targeted test command:

```bash
uv run pytest tests/llm/test_model_config.py tests/llm/test_tool_loop_truncation.py tests/dialectic/test_model_config_usage.py -n0
```

### Alembic migrations

For any file under `migrations/versions/`, create or update a matching verifier under `tests/alembic/revisions/test_<migration_basename>.py`. The pipeline verifies upgrade, downgrade/reversibility, schema, and data expectations through the registry/verifier pattern. Use:

```bash
uv run python scripts/ensure_alembic_tests.py
uv run python scripts/run_alembic_tests.py <changed-files>
```

The bundled `scripts/alembic_test_selector.py` can preview the equivalent command when you are outside pre-commit or reviewing a patch.

### Versioning and release checks

Use `scripts/update_version.py` for multi-component version updates. With no flags it opens an editor; for agents and CI prefer headless flags such as:

```bash
uv run python scripts/update_version.py \
  --api-version X.Y.Z --api-changelog CHANGELOG_SNIPPET.md \
  --python-version A.B.C --python-changelog PY_SDK_CHANGELOG.md \
  --typescript-version A.B.C --typescript-changelog TS_SDK_CHANGELOG.md \
  --yes
```

After version edits, inspect `git diff`, verify the API/Python SDK/TypeScript SDK versions that were meant to change, refresh `uv.lock` when package metadata changed, run targeted SDK/API checks, and only then create tags or publish packages with explicit user approval.

## Release-Safe Final Sweep

Before handoff on a maintenance task, report:

- Files changed and which change surface each belongs to.
- Invariants checked from `maintenance-invariants.md`.
- Commands run and their results.
- Commands intentionally skipped, with constraints such as missing Bun, missing Docker/Postgres, missing provider keys, or user-declined cost.
- Remaining release actions that require human approval, such as tags, package publishing, migrations against a real database, or live LLM verification.
