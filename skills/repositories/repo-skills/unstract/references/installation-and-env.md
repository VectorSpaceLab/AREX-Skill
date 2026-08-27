# Installation And Environment Matrix

Use the smallest environment that covers the workflow you are actually doing. The repo is split into multiple Python packages plus a frontend toolchain, so there is no single universal install command.

## Quick Rules

- Python services and shared packages target Python 3.12.
- Use `uv sync` inside the service or package directory that owns the workflow.
- Use `bun install` in the frontend directory.
- Full-stack local deployment needs Docker plus the service env files.
- Prefer the bundled smoke checker in this skill for shared-package import checks.

## Workflow Matrix

| Workflow | Install / setup | Key env vars | Safe smoke check |
| --- | --- | --- | --- |
| Backend API and hosted MCP | `cd backend && uv sync` | `DJANGO_SETTINGS_MODULE=backend.settings.test`, `DB_SCHEMA=public`, `DJANGO_SECRET_KEY`, `ENCRYPTION_KEY`, `CELERY_BROKER_BASE_URL`, `CELERY_BROKER_USER`, `CELERY_BROKER_PASS`, `SYSTEM_ADMIN_USERNAME`, `SYSTEM_ADMIN_PASSWORD`, `SYSTEM_ADMIN_EMAIL`, `ENABLE_LOG_HISTORY`, `STRUCTURE_TOOL_IMAGE_URL`, `STRUCTURE_TOOL_IMAGE_NAME`, `STRUCTURE_TOOL_IMAGE_TAG`, `MCP_PLATFORM_SERVER_ENABLED` | `python scripts/check_unstract_packages.py --backend` |
| Platform service | `cd platform-service && uv sync` | service `.env`, `UPLOAD_FOLDER`, database credentials, `DB_SCHEMA`, `PLATFORM_SERVICE_HOST`, `PLATFORM_SERVICE_PORT` | import `unstract.platform_service.run` or use the service-specific launcher help |
| Runner service | `cd runner && uv sync` | runner `.env`, container/image and backend connection settings | launcher help / config inspection |
| x2text service | `cd x2text-service && uv sync` | `PLATFORM_SERVICE_HOST`, `PLATFORM_SERVICE_PORT`, `PLATFORM_SERVICE_API_KEY`, `DB_SCHEMA`, `X2TEXT_HOST`, `X2TEXT_PORT` | import `app.config` / service launcher |
| Workers | `cd workers && uv sync` | `INTERNAL_API_BASE_URL`, `INTERNAL_SERVICE_API_KEY`, `CELERY_BROKER_URL`, worker-specific queue and health-port envs, PG-queue overrides when enabled | worker-specific launcher help or worker-module import checks |
| Shared SDK packages | `cd unstract/sdk1 && uv sync --group test`, plus `cd unstract/connectors && uv sync` or the package you need | Optional extras such as AWS/GCS/Azure for `unstract-sdk1`; connector credentials for live connector tests | `python scripts/check_unstract_packages.py` |
| Tool registry and sandbox | `cd unstract/tool-registry && uv sync` and `cd unstract/tool-sandbox && uv sync` if you need local inspection of those packages | `TOOL_REGISTRY_CONFIG_PATH`, `TOOL_REGISTRY_STORAGE_CREDENTIALS`, `UNSTRACT_RUNNER_HOST`, `UNSTRACT_RUNNER_PORT` | `python scripts/check_unstract_packages.py --tool-registry` |
| Frontend | `cd frontend && bun install` | `VITE_BACKEND_URL`, `VITE_ENABLE_POSTHOG`, `VITE_FAVICON_PATH`, `VITE_CUSTOM_LOGO_URL`, `PORT`, `WDS_SOCKET_PORT` | `bun run build` |
| Tool examples | install the relevant shared Python packages first, then the tool's `requirements.txt` | `PLATFORM_SERVICE_HOST`, `PLATFORM_SERVICE_PORT`, `PLATFORM_SERVICE_API_KEY`, `EXECUTION_DATA_DIR`, and tool-specific settings/runtime vars | run the tool's `SPEC` / `PROPERTIES` / `RUN` commands with tiny fixtures |
| Test rig | `cd tests && python -m tests.rig validate` or use the repo's `tox` envs | `UNSTRACT_LLM_MOCK_RESPONSE`, runtime-specific `UNSTRACT_*_URL` values, `UNSTRACT_E2E_RUNTIME` | `python -m tests.rig list-groups` |

## Common Environment Defaults

The following defaults recur across the repo and are useful for safe inspection runs:

- `DJANGO_SETTINGS_MODULE=backend.settings.test`
- `DB_SCHEMA=public`
- `DJANGO_SECRET_KEY=test-secret-key-not-for-production`
- `ENCRYPTION_KEY` set to a placeholder of the right shape
- `CELERY_BROKER_BASE_URL=redis://localhost:6379`
- `CELERY_BROKER_USER=guest`
- `CELERY_BROKER_PASS=guest`
- `SYSTEM_ADMIN_USERNAME=admin`
- `SYSTEM_ADMIN_PASSWORD=admin`
- `SYSTEM_ADMIN_EMAIL=admin@example.com`
- `ENABLE_LOG_HISTORY=False`
- `STRUCTURE_TOOL_IMAGE_URL=docker:test`
- `STRUCTURE_TOOL_IMAGE_NAME=test-structure-tool`
- `STRUCTURE_TOOL_IMAGE_TAG=test`
- `WORKFLOW_EXECUTION_DIR_PREFIX=/tmp/unstract-workflow-exec`

## Notes By Surface

### Backend and MCP
- `backend/settings/base.py` is the source of truth for required env vars and default ports.
- The hosted MCP platform server is off by default and must be enabled explicitly.
- Use the test settings module for import checks so the repo's route modules can load without a live platform.

### Frontend
- The frontend reads runtime config from `window.RUNTIME_CONFIG` first and `VITE_*` env vars second.
- If you change `.env` values, regenerate the runtime config before testing the production build.

### Workers
- The worker launcher multiplexes multiple worker types, PG-queue roles, and health ports from one CLI.
- Keep the backend and `workers/` import order consistent so `plugins` does not resolve from the wrong package root.

### Tooling and registries
- `ToolRegistry` expects `TOOL_REGISTRY_CONFIG_PATH` to point at a config directory containing the registry and JSON outputs.
- Tool example containers read input and output through the protocol described in `tool protocol` references; they are not ordinary Python CLIs.

### Test rig
- The rig is a manifest-driven selector: groups, dependencies, and critical paths are data, not code.
- `UNSTRACT_LLM_MOCK_RESPONSE` is required for execute-path e2e flows that should not hit a live provider.
