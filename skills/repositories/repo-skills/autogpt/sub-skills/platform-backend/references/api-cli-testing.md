# Backend API, CLI, and Testing

## Setup and package notes

Work from `autogpt_platform/backend`. Use `poetry run` for commands that need backend dependencies. The backend package metadata is sdist-oriented; if a wheel/editable install fails in an inspection environment, prefer Poetry's normal project workflow in the checkout rather than treating that as a source error.

```bash
cd autogpt_platform/backend
poetry install
poetry run cli --help
```

## Service entry points

Poetry scripts include:

| Script | Purpose |
| --- | --- |
| `app` | Run the full backend process set |
| `rest` | Run REST API service |
| `ws` | Run WebSocket service |
| `scheduler`, `executor`, `batch-executor` | Run selected worker services |
| `notification`, `platform-linking-manager` | Run support services |
| `copilot-bot`, `copilot-executor` | Run CoPilot support services |
| `cli` | Development/admin CLI with `chat`, `gen-encrypt-key`, `start`, `stop`, and `test` |
| `export-api-schema` | Export OpenAPI JSON for frontend generation |
| `oauth-tool` | OAuth helper CLI |
| `gen-prisma-stub` | Generate Prisma type stubs |

`cli start` writes a PID under the user's config directory and spawns the full app. Prefer foreground `poetry run app` or a specific service while developing so logs and failures are visible.

## API change sequence

1. Identify the feature router under `backend/api/features/<feature>/` or the external API package.
2. Update Pydantic request/response models and service/data functions in the owning feature.
3. Use `Security()` for auth dependencies that should appear in OpenAPI security metadata.
4. Add focused tests near the changed route. Mock at the boundary where the symbol is used.
5. Export or serve OpenAPI after route/schema changes, then regenerate frontend hooks in `platform-frontend`.

Useful command:

```bash
poetry run export-api-schema --output openapi.json --pretty
```

## Prisma and migrations

Schema changes require coordinated Prisma commands:

```bash
poetry run prisma migrate dev
poetry run prisma migrate deploy
poetry run prisma generate
poetry run gen-prisma-stub
```

Use `migrate dev` for creating a migration locally and `migrate deploy` for applying committed migrations. Confirm the selected database URL before any command that mutates a database. Never run a reset against a live or shared database.

## Tests

Use focused tests before broad suites:

```bash
poetry run pytest path/to/test_file.py::test_name -xvs
poetry run pytest backend/blocks/test/test_block.py -xvs
poetry run test
poetry run pytest path/to/test.py --snapshot-update
```

`poetry run test` uses the repository test harness and can start Docker-based database services. Snapshot updates must be reviewed with a diff before acceptance.

## Format, lint, and type helpers

```bash
poetry run format
poetry run lint
poetry run gen-prisma-stub
```

Follow backend style rules: top-level imports except intentional heavy lazy imports, absolute imports for cross-package modules, Pydantic models for structured data, guard clauses, no linter suppressors, no path leaks in errors, and no raw Prisma objects crossing service boundaries.

## Maintainer scripts

| Script | Use | Default safety |
| --- | --- | --- |
| `scripts/generate_block_docs.py` | Block docs generation | Help/static safe; writes docs when run normally |
| `scripts/run_tests.py` | Test DB + pytest harness | Mutates test DB/containers |
| `scripts/gen_prisma_types_stub.py` | Pyright-friendly Prisma stubs | Writes generated stubs |
| `scripts/generate_views.py` | Analytics SQL views | Requires DB credentials; can mutate DB |
| `scripts/download_transcripts.py` | CoPilot transcript debugging | Credential/data sensitive |
| `scripts/replay_session_trace.py` | Langfuse trace replay | Credential/session-data sensitive |
| `scripts/refresh_anthropic_rates.py` | Rate-card refresh | Network/write side effects |
| `scripts/seed_block_preflight_estimates.py` | Estimate aggregation | DB/read/write depending flags |
