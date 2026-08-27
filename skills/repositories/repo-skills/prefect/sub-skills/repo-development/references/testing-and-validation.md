# Testing and Validation

Start specific, prove the changed behavior, then broaden only when the touched area has shared contracts, generated artifacts, package-build impact, or CI-matrix risk.

## Baseline Commands

Use `uv` for Python dependency and command execution:

```bash
uv sync
uv run pytest tests/path.py -k test_name
uv run pytest tests/path.py -x --tb=short
uv run ruff check --fix path/to/file.py
uv run ruff format path/to/file.py
uv run pre-commit run --files path/to/file.py
```

Use `just` for repository recipes:

```bash
just install
just generate-docs
just docs
```

Do not use `pip install` or `uv pip` for repository dependency management.

## Focused Pytest Selection

| Change type | First pytest target | Broaden when |
| --- | --- | --- |
| Single SDK function or class | Matching `tests/test_*.py` file or `tests/<module>/` | Shared public API, engine, state, settings, or client behavior changes |
| Flow/task engine behavior | `tests/test_flow_engine.py`, `tests/test_task_engine.py`, `tests/engine/` | Sync and async paths or task/flow state behavior both changed |
| Server API/model/orchestration | Matching `tests/server/...` path | Database, orchestration, or lifecycle events are involved |
| Database migration/query | `tests/server/database/` plus resource tests | Query must behave differently on SQLite/PostgreSQL |
| Client SDK | `tests/client/`, affected schemas, and client smoke paths | `prefect-client` package boundary or dependency changes are involved |
| CLI command | Matching `tests/cli/test_*.py` or `tests/cli/<group>/` | Shared CLI utilities, JSON output, or deploy command internals change |
| Settings | `tests/test_settings.py` | New setting requires generated settings types/schema updates |
| Events/automations | `tests/events/` and related server tests only if backend evaluation changes | Event schema/protocol behavior changes |
| Deployments/workers/runner | `tests/deployment/`, `tests/runner/`, `tests/workers/`, targeted CLI deploy tests | Work pools, worker channels, or deployment YAML contracts change |
| Docs examples | markdown-docs or example-specific tests when configured | Generated pages or snippets change |
| UI-v2 | UI-v2 npm checks | Deep UI behavior, API service sync, or Storybook coverage changes |

For quick path suggestions, run the bundled helper from the repository root:

```bash
python ../scripts/select_prefect_tests.py src/prefect/client/orchestration/_flows/client.py client/pyproject.toml
```

The helper prints commands only; it does not run tests or mutate files.

## Test Suite Contracts

- The test directory mirrors `src/prefect/` where practical.
- Tests must be deterministic and should avoid timing, ordering, or external state reliance.
- Prefer real flows, deployments, flow runs, and model operations over mocks. Use mocks for external services and timing-sensitive edges.
- Server and client fixtures should not mix. Server API tests use raw test clients; client-side tests use the full SDK client fixture.
- Database tests run against both SQLite and PostgreSQL in CI. Keep queries and migrations compatible with both.
- Use `@pytest.mark.clear_db` only when a test depends on the database starting empty. To audit whether it is needed, run the test with `--no-clear-db`.
- Reset event assertion clients after fixture setup when the test only wants to count events from the action under test.
- Flow timeout tests must use `@pytest.mark.timeout(method="thread")` because alarm-based pytest timeouts interfere with Prefect's own timeout mechanism.
- Use `retry_asserts` for async event propagation or known transient hosted-client database-lock responses; keep result correctness assertions outside retry loops when retrying HTTP requests.

## CI Matrix Awareness

The Python unit-test workflow groups tests into matrix entries such as:

- `Server Tests`: `tests/server/` and `tests/events/server` excluding database and orchestration subgroups.
- `Database Tests`: `tests/server/database/`.
- `Orchestration Tests: Core`: `tests/server/orchestration/` excluding API subtests.
- `Orchestration Tests: API`: `tests/server/orchestration/api/`.
- `Client Tests: Modules`: module-style tests under `tests/` excluding top-level tests, server, CLI, runner, workers, settings, input, and type-safety paths.
- `Client Tests: Top-Level`: selected top-level client/runtime tests.
- `Client Tests: Execution`: flow/task execution, engines, futures, states, transactions, and waiters.
- `Runner, Worker, Settings, Input, and CLI Tests`: runner, workers, CLI, settings, input, and task runner tests.

When adding, moving, or renaming test files, verify that the repository's CI test-selection matrix still covers the new paths. The bundled `select_prefect_tests.py` helper can suggest likely pytest targets, but CI coverage selection is a separate matrix concern.

## Linting and Pre-Commit

Use targeted formatting/linting while iterating:

```bash
uv run ruff check --fix src/prefect/path.py tests/path.py
uv run ruff format src/prefect/path.py tests/path.py
uv run pre-commit run --files src/prefect/path.py tests/path.py
```

Run broader pre-commit only near finalization or when hooks are affected:

```bash
uv run pre-commit run --all-files
```

Remember that local hooks include ruff check, ruff format, codespell, selected mypy paths, `uv-lock`, generated settings types for settings changes, UI-v2 checks for UI paths, and service-sync for selected server/UI OpenAPI paths.

## Service-Heavy and Opt-In Checks

Treat these as opt-in unless the user explicitly requests them or the bug requires them:

- Full test suite: `uv run pytest tests/`.
- Docker-only tests and image-build checks.
- Postgres-backed local runs that require a running database.
- Integration tests under `integration-tests/`.
- Scripts named like `test-with-postgres`, `test-collection-with-postgres`, `run-integration-flows`, compatibility tests, load tests, and release preparation.
- Long-running `prefect server start` sessions; use `prefect config view` first to inspect current configuration.

If service-backed validation is necessary, state prerequisites explicitly and prefer skip flags such as `--disable-docker-image-builds`, `--exclude-service docker`, and `--exclude-service kubernetes` when appropriate.

## Repro Validation

For issue fixes, create a single deterministic repro under `repros/<issue>.py`, run it with `uv run -s repros/<issue>.py` or with the narrow extra required by the issue, then add focused regression tests. Keep the repro until the user asks to remove it.

## Native Candidate Classification

Safe native candidates:

- The bundled `../scripts/select_prefect_tests.py` helper.
- Focused `uv run pytest tests/path.py -k name` commands.
- Targeted `ruff` and `pre-commit run --files` commands.
- Docs link/lint commands after docs changes.

Reference-only or expensive candidates:

- Release, publishing, draft-release, and integration-release scripts.
- Postgres, Docker, and integration service scripts.
- Full pre-commit and full test suite unless the change requires broad validation.
