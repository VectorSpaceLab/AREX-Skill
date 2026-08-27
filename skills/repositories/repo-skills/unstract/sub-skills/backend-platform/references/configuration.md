# Backend Configuration

This file summarizes the backend's environment contract and the commands that are safe to use when inspecting the backend service.

## Install And Start

The backend package is managed with `uv`.

```bash
cd backend
uv sync
```

For local development, migrations and the Gunicorn server are driven by the backend entrypoint:

```bash
./entrypoint.sh --migrate
./entrypoint.sh --dev
```

## Key Settings

The backend's settings live in `backend/backend/settings/base.py`. Important groups of settings include:

- Database: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_SCHEMA`.
- Celery / broker: `CELERY_BROKER_BASE_URL`, `CELERY_BROKER_USER`, `CELERY_BROKER_PASS`, and `CELERY_BACKEND_DB_NAME`.
- Authentication and session defaults: `DEFAULT_AUTH_USERNAME`, `DEFAULT_AUTH_PASSWORD`, `SYSTEM_ADMIN_USERNAME`, `SYSTEM_ADMIN_PASSWORD`, `SYSTEM_ADMIN_EMAIL`, `SESSION_COOKIE_AGE`.
- File and execution paths: `PROMPT_STUDIO_FILE_PATH`, `WORKFLOW_ACTION_EXPIRATION_TIME_IN_SECOND`, `WORKFLOW_PAGE_MAX_FILES`, `EXECUTION_RESULT_TTL_SECONDS`, `EXECUTION_CACHE_TTL_SECONDS`.
- API / deployment routing: `PATH_PREFIX`, `API_DEPLOYMENT_PATH_PREFIX`, `API_DEPL_PRESIGNED_URL_MAX_FILE_SIZE_MB`.
- Hosted MCP controls: `MCP_PLATFORM_SERVER_ENABLED`, `MCP_BILLABLE_CALL_LIMIT`, `MCP_BILLABLE_WINDOW_SECONDS`.
- Logging and feature flags: `ENABLE_LOG_HISTORY`, `LOG_HISTORY_CONSUMER_INTERVAL`, `LOGS_BATCH_LIMIT`, `LOGS_EXPIRATION_TIME_IN_SECOND`.
- External service endpoints: `PLATFORM_SERVICE_HOST`, `PLATFORM_SERVICE_PORT`, `X2TEXT_HOST`, `X2TEXT_PORT`, `FLIPT_BASE_URL`.

## Safe Inspection Defaults

The bundled smoke checker uses test-friendly defaults for the settings that the backend import path expects. Those defaults are safe because they:

- keep the backend on test settings,
- avoid real credentials,
- and avoid real database / broker values while still letting the route modules import.

## Smoke Check

Use the shared checker from the root of this skill tree:

```bash
python ../../scripts/check_unstract_packages.py --backend
```

It verifies the shared package versions, imports the backend URL and MCP modules, and prints the key routing flags.
