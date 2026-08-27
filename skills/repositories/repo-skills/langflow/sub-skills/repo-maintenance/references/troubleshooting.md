# Repo Maintenance Troubleshooting

Use this when a maintenance command fails before moving to a broader or riskier workaround.

## Install and Import Failures

### `uv` or npm is missing

Signal:

```text
uv is not installed. Aborting.
NPM is not installed. Aborting.
```

Fix: install the missing tool, then run `make check_tools`. Keep Node.js at `>=20.19.0` and npm at `>=10.9`. On Windows, use WSL or a dev container for the Linux-oriented Make workflow.

### Package-local tests cannot import test dependencies

Signal examples:

```text
ModuleNotFoundError: No module named 'fakeredis'
pytest: error: unrecognized arguments from package config
```

Fix: sync the package dev group before tests:

```bash
uv sync --group dev --package langflow-base
cd src/lfx && uv sync --dev
cd src/sdk && uv sync --dev
```

Then re-run the focused test.

### `langflow --help` or CLI import fails on optional provider packages

Signal examples:

```text
ModuleNotFoundError: No module named 'openai'
ImportError while importing voice or provider modules
```

Fix: use the development environment that includes the current CLI import requirements or install the missing optional package for the task. Do not add a broad provider dependency to runtime metadata just to satisfy a local check; first confirm whether the import path should be lazy or guarded.

### Torch, transformers, GPU, or local model failures

Signal examples:

```text
PyTorch was not found
transformers model execution unavailable
CUDA driver not found
```

Fix: ordinary repo maintenance does not require local model execution. Skip GPU/transformer execution checks unless the task explicitly targets local models. Keep static checks, unit tests, and import checks separate from heavyweight optional runtime tests.

## Data, Config, and Schema Failures

### Environment file or settings mismatch

Signal examples:

```text
Loading environment from '.env'
setting value is ignored
service uses stale flag after env-file change
```

Fix: verify which command supplies configuration. `make backend` passes `--env-file` to Uvicorn and uses variables such as `port`, `workers`, and `env`. Avoid module-level settings reads in backend code that should respect runtime env-file values; validate with the backend-runtime sub-skill when implementation changes are needed.

### Flow/schema validation fails after package or component changes

Signal examples:

```text
component-not-found-with-hint
component-name-ambiguous
field required
Output method not found
```

Fix: decide whether this is component authoring, migration-table, or flow JSON behavior. For migration-table changes, run extension migration guards. For component class or output method issues, route to component-development. For flow JSON normalization, route to flow-authoring or SDK/API clients.

### Migration autogenerate proposes destructive operations

Signal examples:

```text
Detected removed table
Detected removed column
alembic check reports pending operations
```

Fix: inspect the migration before applying it. Prefer explicit rename/backfill logic over accepting generated drop/create operations. Run focused Alembic tests and never upgrade or downgrade a real user database without backup and approval.

## CLI and API Misuse

### Make target gets ignored arguments

Signal examples:

```text
pytest did not select the intended test
make: *** No rule to make target 'path/to/test.py'
```

Fix: pass pytest arguments through `args="..."` for backend, LFX, or SDK Make wrappers:

```bash
make unit_tests args="src/backend/tests/unit/services/authorization/test_guards.py -q" async=false
make lfx_test args="tests/unit/cli/test_validate_command.py -q"
make sdk_test args="tests/test_serialization.py -q"
```

Frontend file selection uses the positional Make pattern:

```bash
make test_frontend_file src/__tests__/example.test.tsx
```

### `make lint` does not run mypy

Signal:

```text
No type checker configured.
```

Fix: do not treat `make lint` as a type-check result. Use Ruff checks, package-specific lint targets, or an explicit type-check command if a task introduces one. For frontend TypeScript, use the frontend package scripts or build/type-check flow if needed.

### API example execution fails with connection errors

Signal examples:

```text
ECONNREFUSED localhost:7860
Connection refused
401 Unauthorized
```

Fix: use syntax-only checks unless a Langflow server is intentionally running. For live examples, start a local server and supply only safe local credentials. A `401` usually means the example needs an API key or auth configuration; do not paste secrets into docs or tests.

## Backend, Runtime, Service, Credential, and Network Boundaries

### Authorization tests fail after guard edits

Signal examples:

```text
expected 403 got 404
cross-user fetch widened visibility
filter_visible_resources leaked candidate
```

Fix: test service-level guard behavior first, then route fetch behavior. Check that owner-scoped queries remain owner-scoped when authorization plugins do not support cross-user fetch, and that plugin-enabled paths immediately call `ensure_*_permission`. Preserve 403-to-404 privacy where route helpers intentionally hide UUID existence.

### Database tests fail only in a full batch

Signal examples:

```text
passes alone, fails under -n auto
fixture state leaked
SQLite database locked
```

Fix: re-run the focused test sequentially with `async=false` or plain `uv run pytest ... -q`. If the focused test passes, note the batch flake and avoid changing unrelated code. If it fails alone, inspect fixtures and transaction boundaries.

### Provider, network, or credential tests fail

Signal examples:

```text
api_key_required test failed
HTTP 401/403 from provider
network timeout
```

Fix: do not convert missing credentials into code changes. Skip credentialed tests unless credentials were intentionally provided. Prefer mock-free real integration tests only when the environment has the required provider, network, and safety approval.

### Docker, publish, or cloud commands are accidentally requested

Signal examples:

```text
uv publish prompts for credentials
Docker daemon unavailable
cloud CLI wants login
```

Fix: stop and confirm intent. Publishing and cloud deployment are side-effectful. Repo maintenance may document or dry-check metadata, but production deployment belongs to deployment-and-operations and publishing requires explicit release authorization.

## Frontend Workflow Failures

### `node_modules` missing or stale

Signal examples:

```text
Frontend dependencies not found. Installing...
Cannot find module '@biomejs/biome'
Vite dependency pre-bundle error
```

Fix:

```bash
make install_frontend
make format_frontend_check
```

If stale caches persist:

```bash
make clean_frontend_build
make run_clic
```

Use `make install_frontendc` only when a clean npm install is acceptable because it removes `node_modules` and `package-lock.json` before reinstalling.

### Playwright fails before running tests

Signal examples:

```text
browser executable not found
Playwright host dependencies are missing
```

Fix: report Playwright as skipped unless the task requires e2e browser validation. Jest and Biome are usually sufficient for non-browser UI code changes.

### Frontend build succeeds but packaged app serves old UI

Signal: Vite dev server shows the change, but `langflow run` or `make run_cli` serves stale static files.

Fix: rebuild and copy frontend assets into the backend static frontend:

```bash
make clean_frontend_build
make build_frontend
make run_cli
```

## Generated File and CI Guard Failures

### Deprecated LangChain imports are reported

Signal:

```text
Uses deprecated 'langchain.schema' - use 'langchain_core.messages'
```

Fix: update imports to the suggested package path when the replacement matches the imported symbol. If a provider package moved a class to `langchain_community` or another extension package, ensure the dependency is declared where that code lives.

### Migration table append-only check fails

Signal:

```text
entry removed
entry target changed
ambiguous_bare_names candidates shrunk
```

Fix: restore the original entry and append a new entry instead. Published migration mappings protect saved flows, so mutation is a compatibility break.

### Bundle API changelog guard fails

Signal:

```text
in-scope BUNDLE_API surface changed but BUNDLE_API.md was not updated
```

Fix: add a concise changelog entry for the public bundle API change. If the changed file should not be in scope, review the guard list deliberately rather than bypassing it.

### Router trust guard fails

Signal:

```text
forbidden route under /api/v1/extensions
install / uninstall / registry mutation route found
```

Fix: do not expose runtime install/uninstall/registry mutation under live extension routes. Move mutation to offline tooling or privileged maintainer commands.

## Escalation Checklist

Before escalating, capture:

- Exact command and working directory.
- First failure line and exit code.
- Whether dependencies were synced for the correct package.
- Whether the check was focused, package-level, broad, credentialed, or destructive.
- Safe next command or reason to ask the user before proceeding.
