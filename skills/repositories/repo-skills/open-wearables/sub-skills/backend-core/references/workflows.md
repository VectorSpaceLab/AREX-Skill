# Backend Workflows

This reference gives concrete commands and safe sequencing for backend development. Commands assume you are at the repository root unless a `cd backend` command is shown.

## Local stack and service commands

### Docker Compose stack

```bash
# Build images from scratch
make build

# Start in detached mode
make run

# Start in foreground
make up

# Watch mode with sync/restart rules
make watch

# Stop or remove services
make stop
make down
```

Primary service endpoints:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Swagger/OpenAPI UI: `http://localhost:8000/docs`
- Flower: `http://localhost:5555`
- Svix server (when enabled/configured): `http://localhost:8071`

Docker service names and common logs:

```bash
docker compose logs -f app
docker compose logs -f celery-worker
docker compose logs -f celery-beat
docker compose logs -f redis
docker compose logs -f svix-server
```

### Backend package workflow

```bash
cd backend

# Create/sync the backend uv environment
uv sync

# Include dev/test dependencies
uv sync --group dev

# Include code-quality tools
uv sync --group code-quality

# Run the API locally after DB/Redis are available
uv run fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

Python requirement: `>=3.13`. Backend package name/version: `open-wearables==0.7.0`. Core dependencies include FastAPI, SQLAlchemy 2.0, psycopg, Pydantic settings, Celery, Redis, Sentry, Alembic, httpx, requests, boto3, Svix, bcrypt, cryptography, Faker, numpy, and provider parsing/auth packages.

## Quality checks

Run the smallest relevant commands first, then broaden only when the task scope warrants it.

```bash
# Static skill/repo drift checker; read-only and safe
python skills/disco/open-wearables/sub-skills/backend-core/scripts/check_backend_core.py --repo-root .

# Optional OpenAPI import/docs navigation check; no network/writes, but imports backend dependencies
python skills/disco/open-wearables/sub-skills/backend-core/scripts/check_backend_core.py --repo-root . --import-openapi

# Backend formatting/linting
cd backend
uv run ruff check . --fix
uv run ruff format .

# Type check
uv run ty check .

# Backend tests
uv run pytest -q
uv run pytest -v --cov=app
```

For a change, prefer focused test sets:

```bash
# Users, auth, credentials
cd backend
uv run pytest tests/api/v1/test_users.py tests/api/v1/test_api_keys.py tests/api/v1/test_applications.py tests/api/v1/test_auth.py -q

# Summaries / events / timeseries
uv run pytest tests/api/v1/test_summaries.py tests/api/v1/test_workouts.py tests/api/v1/test_sync_status.py tests/services/test_time_series_service.py -q

# Outgoing webhooks
uv run pytest tests/api/v1/test_outgoing_webhooks.py tests/tasks/test_webhook_push_task.py -q

# Seed data
uv run pytest tests/api/v1/test_seed_data.py tests/services/test_seed_data_service.py -q

# Repositories and model-adjacent behavior
uv run pytest tests/repositories -q
```

Backend tests default to testcontainers for PostgreSQL and Redis. If you already have disposable test services, set `TEST_DATABASE_URL` and `TEST_REDIS_URL` before running pytest to avoid starting containers.

## Database migrations

### Docker path

```bash
# Apply all migrations inside the app container
make migrate

# Create a migration; m is required
make create_migration m="Add new table or column"

# Roll back one revision
make downgrade
```

### Local backend path

```bash
cd backend
uv run alembic revision --autogenerate -m "Description of change"
uv run alembic upgrade head
uv run alembic downgrade -1
```

Migration rules:

1. Change SQLAlchemy models first.
2. Generate and inspect Alembic output; do not blindly trust autogenerate for enum changes, partial indexes, JSONB, foreign-key cascades, or data migrations.
3. For model changes that affect API payloads, update Pydantic schemas and response tests in the same change.
4. Seed scripts initialize provider settings, device priorities, series types, webhook event types, admin account, archival settings, and several idempotent legacy data fixes during app startup.
5. Destructive utilities such as database reset or production data-migration scripts are not verification steps. Use only with explicit disposable-DB intent.

## Adding or changing an endpoint

1. Choose the route family in [api-routes.md](api-routes.md). Decide whether the endpoint is `External:`, `Internal:`, or `System:`.
2. Define request and response schemas. Use clear field bounds and descriptions for query/body parameters.
3. Implement service logic. If new DB access is required, add a repository method that returns ORM rows or primitives.
4. Add/adjust models and migrations if persistence changes.
5. Register the route in the v1 router with the correct prefix/tag. Keep module routers prefix-free.
6. Add tests for success, auth failure, validation failure, not found, and side effects.
7. If the route tag begins `External:`, update the API Reference tab in `docs/docs.json` with the exact endpoint page string, for example `GET /api/v1/users/{user_id}/summaries/body`.
8. Coordinate caller updates with [frontend-portal](../../frontend-portal/SKILL.md) or [mcp-server](../../mcp-server/SKILL.md) if the endpoint is consumed there.
9. Run the safe checker and focused tests. Include `--import-openapi` when import-time config is ready so docs navigation drift is caught.

Minimal route pattern:

```python
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.database import DbSession
from app.schemas.example import ExampleCreate, ExampleRead
from app.services import ApiKeyDep, example_service

router = APIRouter()


@router.post("/users/{user_id}/examples", status_code=status.HTTP_201_CREATED, response_model=ExampleRead)
def create_example(
    user_id: UUID,
    payload: ExampleCreate,
    db: DbSession,
    _api_key: ApiKeyDep,
    notify: Annotated[bool, Query(description="Whether to emit notifications.")] = False,
) -> ExampleRead:
    return example_service.create_for_user(db, user_id, payload, notify=notify)
```

## Adding or changing a service/repository/model

1. Add or update the ORM model with `Mapped[...]` annotations and shared mapping aliases.
2. Add schema types: external create/update/read and internal create/update when server-generated fields are needed.
3. Add repository query methods for database operations only. Avoid Pydantic input/output in repositories.
4. Add a service method that composes repositories and emits side effects.
5. Expose a singleton service instance when existing routes import service singletons.
6. Add repository/service tests. Use factories and the transactional `db` fixture.
7. If service code catches and suppresses errors in batch/background paths, use the Sentry helper pattern so errors are logged and captured.

Service pattern:

```python
from logging import Logger, getLogger
from uuid import UUID

from app.database import DbSession
from app.models import Example
from app.repositories.example_repository import ExampleRepository
from app.schemas.example import ExampleCreateInternal, ExampleUpdateInternal
from app.services.services import AppService


class ExampleService(AppService[ExampleRepository, Example, ExampleCreateInternal, ExampleUpdateInternal]):
    def __init__(self, log: Logger, **kwargs):
        super().__init__(crud_model=ExampleRepository, model=Example, log=log, **kwargs)

    def count_for_user(self, db: DbSession, user_id: UUID) -> int:
        return self.crud.count_for_user(db, user_id)


example_service = ExampleService(log=getLogger(__name__))
```

Repository pattern:

```python
from uuid import UUID
from sqlalchemy import func

from app.database import DbSession
from app.models import Example
from app.repositories.repositories import CrudRepository
from app.schemas.example import ExampleCreateInternal, ExampleUpdateInternal


class ExampleRepository(CrudRepository[Example, ExampleCreateInternal, ExampleUpdateInternal]):
    def count_for_user(self, db: DbSession, user_id: UUID) -> int:
        return db.query(func.count(self.model.id)).filter(self.model.user_id == user_id).scalar() or 0
```

## Working with auth/API keys/applications

- Use `POST /api/v1/auth/login` with OAuth2 form fields `username` and `password` for developer JWTs.
- Use developer JWTs to create API keys: `POST /api/v1/developer/api-keys` with optional JSON `{"name": "..."}`.
- Use `X-Open-Wearables-API-Key: sk-...` for external data API calls.
- API-key validation returns 401 `Invalid or missing API key`; missing credentials return 401 `Authentication required: provide JWT token or API key`.
- App credentials are separate from API keys. Application creation returns a one-time `app_secret`; rotation invalidates the old secret.
- Refresh tokens are opaque `rt-...` ids and rotate on every refresh.

Safe local curl examples against a running dev API:

```bash
# Login as seeded admin (use your dev credentials, not production secrets)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=your-secure-password"

# Create an API key with a developer JWT
curl -X POST http://localhost:8000/api/v1/developer/api-keys \
  -H "Authorization: Bearer <developer-jwt>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Local dev key"}'

# List users with an API key
curl http://localhost:8000/api/v1/users \
  -H "X-Open-Wearables-API-Key: <api-key>"
```

## Working with summaries, events, and timeseries

- Use Open Wearables UUID user ids, never deprecated external ids, for data endpoints.
- Use ISO 8601 timestamps with time zones for `start_date`, `end_date`, `start_time`, and `end_time`.
- Timeseries `types` is a repeated query parameter: `?types=heart_rate&types=steps`.
- Keep cursor pagination stable by using the provided `next_cursor` and `previous_cursor`; do not invent offset pagination for cursor endpoints.
- When adding a new `SeriesType`, update series type definitions, seeding, provider coverage, docs/data-type content, mappings from series type to webhook events if needed, and summary/service aggregation code if it affects public summaries. Provider coverage additions should be coordinated with [provider-integrations](../../provider-integrations/SKILL.md).
- When adding an event category, update detail model/registry, event service queries, response schemas, delete behavior, outgoing webhook event types if public, and docs/API navigation if exposed as an external endpoint.

Example reads:

```bash
curl "http://localhost:8000/api/v1/users/<user-id>/timeseries?start_time=2026-01-01T00:00:00Z&end_time=2026-01-02T00:00:00Z&types=heart_rate&limit=50" \
  -H "X-Open-Wearables-API-Key: <api-key>"

curl "http://localhost:8000/api/v1/users/<user-id>/summaries/activity?start_date=2026-01-01T00:00:00Z&end_date=2026-01-08T00:00:00Z&sort_order=desc" \
  -H "X-Open-Wearables-API-Key: <api-key>"
```

## Working with sync status and background tasks

- Celery worker command in Docker runs queues `default,sdk_sync,garmin_sync,webhook_sync` with thread pool.
- Celery beat removes stale `celerybeat.pid` then starts scheduler.
- Pull sync task filters connections by provider settings and capability. Live sync polls providers in `pull` mode; historical sync can use REST for all `rest_pull` providers.
- Async `POST /providers/{provider}/users/{user_id}/sync` rejects provider-specific flags when `async=true`; use `async=false` for per-provider flag tests.
- Use sync status helpers to emit `started`, `progress`, `completed`, `failed`, or `cancelled`; errors while emitting should never abort data sync.
- SSE responses require proxy-friendly headers: `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no`, `Connection: keep-alive`.

Manual sync-status smoke against a running dev API:

```bash
curl -N "http://localhost:8000/api/v1/users/<user-id>/sync/stream?replay=20" \
  -H "X-Open-Wearables-API-Key: <api-key>"

curl "http://localhost:8000/api/v1/users/<user-id>/sync/runs?limit=20" \
  -H "X-Open-Wearables-API-Key: <api-key>"
```

## Working with outgoing webhooks

- Default local deployments have outgoing webhooks disabled. Endpoint management returns 503 until `OUTGOING_WEBHOOKS_ENABLED=true` and Svix auth is configured.
- `svix-server` is part of Docker Compose and uses PostgreSQL database `svix` plus Redis db 1.
- `SVIX_AUTH_TOKEN` can be provided directly; otherwise it is derived from `SVIX_JWT_SECRET`, which defaults to `SECRET_KEY` in compose entrypoint behavior.
- Startup registration of event types is idempotent and non-fatal. If Svix starts slowly, registration retries on next boot.
- Event management endpoints accept HTTP(S) URLs and optional event-type filters. Use placeholders in docs/tests; never commit real webhook targets or secrets.

Useful local checks:

```bash
# Inspect whether backend exposes the feature flag
auth_header="Authorization: Bearer <developer-jwt>"
curl http://localhost:8000/api/v1/config -H "$auth_header"

# List webhook event types when the API is running
curl http://localhost:8000/api/v1/webhooks/event-types -H "X-Open-Wearables-API-Key: <api-key>"
```

## Seed data workflow

```bash
# Docker/disposable dev DB; mutates database
make seed

# Direct API dispatch with developer JWT; mutates database via Celery
curl -X POST http://localhost:8000/api/v1/settings/seed \
  -H "Authorization: Bearer <developer-jwt>" \
  -H "Content-Type: application/json" \
  -d '{"num_users":1,"profile":{"preset":"minimal"},"random_seed":12345}'
```

Seed generation is intended for local demos, staging, and tests. It creates users, connections, events, time-series rows, and health scores. Never run it against a production database unless explicitly requested by an operator who understands the mutation.

## Safe bundled checker

The bundled checker is intentionally read-only:

```bash
python skills/disco/open-wearables/sub-skills/backend-core/scripts/check_backend_core.py --help
python skills/disco/open-wearables/sub-skills/backend-core/scripts/check_backend_core.py --repo-root .
python skills/disco/open-wearables/sub-skills/backend-core/scripts/check_backend_core.py --repo-root . --json
```

What it checks by default:

- Expected backend source directories and important route/service/model/schema/test files exist.
- Backend `pyproject.toml` advertises Python 3.13+ and core backend dependencies.
- v1 route module inventory contains the expected backend-core route modules.
- `docs/docs.json` has an API Reference tab and endpoint page strings.
- Required native backend test candidate files exist.

With `--import-openapi`, it imports the backend app using harmless fallback env values when needed, counts OpenAPI paths, captures warnings, and compares `External: *` OpenAPI paths to `docs/docs.json`. It still does not contact live services or write files.
