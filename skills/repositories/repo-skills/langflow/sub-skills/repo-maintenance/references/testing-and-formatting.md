# Testing and Formatting

Choose the smallest command that proves the changed behavior, then broaden only when the change crosses package boundaries or generated artifacts.

## Selection Heuristic

1. Run static syntax or helper checks for new or edited scripts.
2. Run the closest unit test file or test directory for the changed module.
3. Run the package-level test command for cross-module changes.
4. Run broad `make tests`, frontend e2e, integration tests, or docs builds only when the task actually touches those surfaces or the user asks for final full validation.

Avoid credentialed, network, GPU, browser, Docker, or destructive database checks by default. Prefer reporting a skipped check with the concrete prerequisite over forcing unsafe setup.

## Backend Python Checks

Backend tests live under `src/backend/tests`. Root unit tests default to excluding credentialed provider tests:

```bash
make unit_tests
make unit_tests async=false
make unit_tests args="src/backend/tests/unit/api/v1/test_flows.py -q" async=false
uv run pytest src/backend/tests/unit/services/authorization/test_guards.py -q
uv run pytest src/backend/tests/unit/alembic/test_migration_validator.py -q
```

`make unit_tests` uses parallel execution by default and tracks durations. Use `async=false` when order, database setup, debugging, or failure logs are easier to inspect sequentially. Use `args="..."` to pass a focused pytest selection through the Make target.

Markers and safety:

- `api_key_required`: external credentials are needed; skip unless explicitly provisioned.
- `no_blockbuster`: used where the blocker plugin should not apply.
- `security`: security regression checks such as IDOR/auth/access control.
- Database tests can fail in full batches but pass individually; isolate before assuming a code regression.

When editing authorization guards, start with service-level authz tests before route-level and broad tests:

```bash
uv run pytest src/backend/tests/unit/services/authorization/test_guards.py -q
uv run pytest src/backend/tests/unit/services/authorization/test_flow_route_guards.py -q
uv run pytest src/backend/tests/unit/services/authorization/test_domain_resolution.py -q
uv run pytest src/backend/tests/unit/services/authorization/test_filter_visible.py -q
uv run pytest src/backend/tests/unit/api/v1/test_authz_share_routes.py -q
```

If a route fetch path changed, add the relevant API route test and verify privacy behavior for 403-to-404 conversions where applicable.

## LFX Package Checks

Use root wrappers for normal maintenance or package-local Make targets for isolated LFX work:

```bash
make lfx_test args="tests/unit/cli/test_validate_command.py -q"
make lfx_format
make lfx_lint
cd src/lfx && uv sync --dev
cd src/lfx && uv run --package lfx pytest tests/unit/cli/test_run_command.py -q
cd src/lfx && make release_check
```

Use LFX tests for executor CLI, extension manifests, bundle migration, `lfx run`, `lfx serve`, MCP, runtime variables, and package-level flow validation. Some integration tests require provider dependencies or credentials; keep to `tests/unit` unless the task explicitly targets integration behavior.

## SDK Package Checks

Use SDK tests for REST client models, serialization, push/pull, file I/O, background jobs, and streaming helpers:

```bash
make sdk_test args="tests/test_serialization.py -q"
make sdk_format
make sdk_lint
cd src/sdk && uv sync --dev
cd src/sdk && uv run pytest tests/test_models.py tests/test_serialization.py -q
```

SDK integration tests require a live Langflow instance. Do not start services or use credentials unless the task needs a real client/server path.

## Frontend Checks

Frontend dependencies are managed under `src/frontend`. Node.js must satisfy the declared engine range.

```bash
make install_frontend
make format_frontend
make format_frontend_check
make test_frontend
make test_frontend_file src/__tests__/path/to/test.test.tsx
make test_frontend_pattern "renders flow"
make tests_frontend
make build_frontend
```

Use `make test_frontend` for Jest unit tests and `make tests_frontend` for Playwright e2e tests. Playwright may need browser installation and can be slower; skip it unless UI routing, graph workspace behavior, or e2e browser behavior changed. Use `make test_frontend_file` or `make test_frontend_pattern` while iterating.

Formatting and linting split:

- `make format_frontend` runs the frontend formatter.
- `make format_frontend_check` runs a Biome check without writing changes.
- `make build_frontend` compiles Vite output and copies it into the backend static frontend directory.

If frontend build output is stale or mismatched, run:

```bash
make clean_frontend_build
make build_frontend
```

## Formatting and Linting

Backend formatting:

```bash
make format_backend
uv run ruff check path/to/file.py --fix
uv run ruff format path/to/file.py
```

`make format_backend` runs Ruff fixes and formatting across the workspace. Use path-scoped Ruff commands for small edits when broad formatting would touch unrelated files.

Root lint target currently installs backend dependencies and prints that no type checker is configured. Do not claim a mypy/type-check run happened unless a task adds or invokes a real type-check command.

Codespell:

```bash
make codespell
make fix_codespell
```

Use spelling checks for docs, user-facing strings, or large prose changes.

## Integration and Broad Checks

Run broad checks when the change crosses multiple packages or before release handoff:

```bash
make tests
make integration_tests_no_api_keys
make integration_tests
make docs_build
make build
```

`make tests` runs backend unit tests, backend integration tests, and coverage. This is expensive and can require optional dependencies or services; prefer focused tests during iteration.

Integration tests can require API keys, network, databases, or providers. Start with `make integration_tests_no_api_keys` unless credentials are explicitly available and safe.

## Migration Checks

For Alembic changes:

```bash
make alembic-check
uv run pytest src/backend/tests/unit/alembic/test_migration_validator.py -q
uv run pytest src/backend/tests/unit/alembic/test_migration_execution.py -q
uv run pytest src/backend/tests/unit/alembic/test_existing_migrations.py -q
```

For extension migration tables and bundle API changes, verify the static invariants from [maintainer-checks.md](maintainer-checks.md): unique bare-name mappings, append-only migration entries, no runtime install/uninstall/registry mutation routes under extension APIs, and changelog coverage for public bundle API changes. If an executable guard is required, bundle or adapt it into this skill tree before telling a future agent to run it.

## Script and Helper Checks

For scripts you create or edit:

```bash
python -m py_compile path/to/script.py
python path/to/script.py --help
```

If a script has safe sample input, run it against a tiny temporary fixture instead of the full repo first. A script intended for CI should have clear exit codes, argparse help, deterministic output, and no hidden dependency on local environment paths.

## Validation Handoff Template

Use this compact format when handing off maintenance work:

```text
Validated:
- Static: python -m py_compile ...
- Focused tests: uv run pytest ...
- Formatting: make format_backend / make format_frontend_check
Skipped:
- Playwright: browser deps not installed
- Integration providers: credentials not available
Risk notes:
- Version pins reviewed in root/base/lfx/sdk/frontend metadata
```

Concrete skipped checks are acceptable when they state the missing prerequisite and the narrower checks that still ran.
