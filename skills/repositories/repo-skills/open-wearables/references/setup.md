# Setup and Validation

## Purpose

Read this when preparing an Open Wearables checkout, choosing validation commands, or diagnosing setup drift across backend, frontend, and MCP packages. This reference distills repo commands and package metadata into a single operating checklist.

## Prerequisites

| Surface | Requirement | Notes |
| --- | --- | --- |
| Backend | Python `>=3.13`, `uv`, Docker for native DB/Redis tests | Backend package is `open-wearables==0.7.0`. Native tests use PostgreSQL/Redis via testcontainers unless explicit test URLs are supplied. |
| Frontend | Node `>=22`, pnpm `>=10` | `packageManager` pins pnpm `10.13.1`; Corepack can provide pnpm when it is not on PATH. |
| MCP | Python `>=3.13`, `uv`, backend API URL, API key | MCP package is independent and talks to backend REST endpoints only. |
| Local services | Docker Compose | Starts backend, frontend, PostgreSQL, Redis, Celery worker/beat, Flower, Svix server, and related support services. |

## Safe first checks

From a checkout root:

```bash
python skills/disco/open-wearables/scripts/check_open_wearables_install.py --repo-root .
python skills/disco/open-wearables/sub-skills/backend-core/scripts/check_backend_core.py --repo-root .
python skills/disco/open-wearables/sub-skills/provider-integrations/scripts/provider_inventory.py --check-count
python skills/disco/open-wearables/sub-skills/frontend-portal/scripts/check_frontend_metadata.py --repo-root .
python skills/disco/open-wearables/sub-skills/mcp-server/scripts/check_mcp_config.py --mcp-root mcp --no-import-check
```

These generated helpers are read-only. They do not install dependencies, start listeners, call provider APIs, write docs, mutate databases, or validate live API keys.

## Backend commands

```bash
cd backend
uv sync --group dev --group code-quality
uv run pytest tests/api/v1/test_users.py -q
uv run pytest tests/providers/test_provider_coverage.py -q
uv run ruff check .
uv run ruff format --check .
uv run ty check .
```

Use focused test files first. Expand to `make test` or a broader `uv run pytest` only when the change touches shared fixtures, authentication, provider contracts, database setup, or cross-cutting services.

## Frontend commands

```bash
cd frontend
corepack enable  # if pnpm is not on PATH and policy allows using Corepack
pnpm install --frozen-lockfile
pnpm test
pnpm run lint
pnpm run format:check
pnpm run build
```

The portal reads its backend URL through `VITE_API_URL`. Runtime URL resolution is in the frontend API config reference; do not replace it with direct `import.meta.env` reads in route or component code.

## MCP commands

```bash
cd mcp
uv sync --group dev --group code-quality
cp config/.env.example config/.env  # then replace placeholders before live calls
uv run pytest -q
uv run ruff check .
uv run ty check .
```

`uv run start` starts a long-running MCP server and requires a usable `OPEN_WEARABLES_API_URL` plus `OPEN_WEARABLES_API_KEY`. Prefer mocked tests and the bundled config checker unless the task explicitly requires a live assistant connection.

## Docker stack

Common root commands:

```bash
docker compose up -d
make seed
make stop
make down
```

Use Docker for normal development and for native backend tests that need PostgreSQL/Redis. Treat seed/reset/replay utilities as dev-only. Never run destructive or credential-bound scripts against production data while following this skill.

## Environment variables to know

| Surface | Important variables | Notes |
| --- | --- | --- |
| Backend auth/config | `SECRET_KEY`, `MASTER_KEY`, `API_BASE_URL`, `FRONTEND_URL`, `CORS_ORIGINS` | Generate real secrets outside version control. `MASTER_KEY` controls encryption-sensitive behavior. |
| Backend DB/Redis | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_SSL` | Native tests can also use explicit test URLs when configured. |
| Providers | `<PROVIDER>_CLIENT_ID`, `<PROVIDER>_CLIENT_SECRET`, webhook secrets/tokens | Do not log or commit. Provider setup belongs in `provider-integrations`. |
| Raw payload/AWS | `RAW_PAYLOAD_STORAGE`, `RAW_PAYLOAD_S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | S3/replay workflows require explicit credentials and may involve network/mutation. |
| Frontend | `VITE_API_URL` | Read via runtime config helper; same build can point to different backend hosts. |
| MCP | `OPEN_WEARABLES_API_URL`, `OPEN_WEARABLES_API_KEY`, `LOG_LEVEL`, `REQUEST_TIMEOUT` | MCP appends `/api/v1/...` paths itself; use API base host only. |

## Native verification candidates

After the whole runtime skill is integrated and final verification is authorized, use these native candidates selectively:

- Backend core: selected `backend/tests/api/v1/` and `backend/tests/services/` files for users, auth/API keys/apps, summaries, events, timeseries, sync status, seed data, outgoing webhooks, and tasks.
- Provider integrations: `backend/tests/providers/test_provider_factory.py`, `test_provider_coverage.py`, `test_historical_sync.py`, plus provider-specific integration/import tests.
- Frontend portal: `frontend/src/lib/utils/activity.test.ts`, `frontend/src/lib/utils/format.test.ts`, and broader `pnpm run lint`/`pnpm run build` if dependencies are installed.
- MCP server: `mcp/tests/test_api_client.py` and `mcp/tests/test_tools.py` with mocked HTTP.

Do not treat skipped credential/network/provider-live checks as passes. Record them as explicit limitations when a task depends on real provider APIs or live assistant configuration.
