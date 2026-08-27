# Backend API architecture

This reference distills the backend code and project backend rules into an operating map for future edits. Inspect current source before changing behavior; this document is a starting model, not a substitute for nearby code.

## Scope and boundaries

Use this sub-skill for:

- FastAPI app entry/lifespan, middleware, router inclusion, and health/static serving.
- Routers, service modules, schemas, auth/team dependencies, SQLAlchemy/Alembic, and backend tests.
- Filesystem-backed workspace state exposed by backend endpoints.

Route out of scope:

- Job/provider launch lifecycle and compute-provider dispatch details: `../task-execution-compute/SKILL.md`.
- CLI and SDK package API behavior: `../cli-sdk-workflows/SKILL.md`.
- Frontend fetch hooks, UI auth retries, and visual/browser verification: `../frontend-web-app/SKILL.md`.

## App entry, lifespan, and source-run caveat

- The backend entry point is `api/api.py`, not a packaged `transformerlab.api` module.
- The `FastAPI` app is created in that entry file with a custom lifespan.
- `api/pyproject.toml` builds a minimal package for dependency management; actual backend code runs from the `api/transformerlab/` source tree. Run commands from `api/` when importing or testing backend code.
- `run()` starts uvicorn with the import string `api:app`; HTTPS mode creates or reuses a self-signed cert and can force the asyncio loop.

Startup lifespan performs these backend-wide actions, in order conceptually:

1. Set the default asyncio thread-pool size from `TFL_ASYNC_THREAD_POOL_SIZE`.
2. Print launch/storage banners.
3. Ensure optional storage gateway services and initialize shared directories.
4. Configure the cache service.
5. Validate cloud credentials off the event loop.
6. Initialize the DB and run Alembic migrations.
7. Acquire worker leadership; only the leader starts background workers.
8. Start migration/status/notification/remote-queue/upload cleanup workers when leader.

Shutdown stops leader-owned workers, kills tracked child processes, stops storage gateways, closes DB resources, and performs final cleanup.

Important app-level behavior:

- `/healthz` is unauthenticated and should stay lightweight.
- The React/static app is mounted at `/` after API routers.
- The validation exception handler maps FastAPI `RequestValidationError` into a FastChat-style error body with HTTP 400.
- CORS allows local dev origins by dynamic middleware when no specific frontend origin is configured.
- Static asset cache headers distinguish hashed assets from HTML.

## Router inclusion and protection model

The app includes many routers with `dependencies=[Depends(get_user_and_team)]`, which protects every route on those routers. Some routers are included without a global dependency because they are public, auth-specific, API-key/quota-specific, or manage their own dependencies.

For new protected endpoints:

- Prefer adding `user_and_team: dict = Depends(get_user_and_team)` when the route needs user, team, or role values.
- Use app-level/router-level dependency only when the route does not need the returned user/team object.
- Use `require_team_owner` for owner-only operations and still validate path `team_id` matches the resolved team.
- Keep public endpoints deliberately public and document why; do not accidentally add `get_user_and_team` to anonymous share/auth status endpoints.

## Auth and team context

Auth uses FastAPI Users plus project-specific JWT/cookie/API-key handling.

Primary dependency behavior:

- `_get_user_from_jwt_or_api_key()` tries API key first, then Bearer JWT, then auth cookie.
- `get_user_and_team()` returns `{"user": user, "team_id": team_id, "role": role}` after authenticating and verifying team membership.
- JWT auth requires `X-Team-Id` or the team cookie.
- API-key auth can use an API-key-scoped team, a supplied `X-Team-Id`, or the user's personal team.
- `require_team_owner()` requires owner role and returns the team object too.
- `/users/me/teams` creates a personal team for an existing user if none exists.

Org/team filesystem context:

- App middleware reads `X-Team-Id` or determines team from an API key, calls `lab.dirs.set_organization_id(team_id)`, and clears it at request end.
- `get_user_and_team()` also sets the org id to keep context consistent after dependency resolution.
- The SDK uses `contextvars` for organization/team-scoped workspace directories.
- Context vars do not automatically propagate into new threads or into coroutines scheduled from another thread. If code uses `run_in_executor()` or `asyncio.run_coroutine_threadsafe()`, set `lab.dirs.set_organization_id(team_id)` inside the executed function or scheduled coroutine and clear it in `finally`.

## Routers vs services

Routers should do:

- FastAPI dependency injection (`get_async_session`, `get_user_and_team`, permission dependencies).
- Request/body/query parsing and schema validation.
- Input normalization that is tied to HTTP concerns, such as path traversal checks, filename sanitation, response models, and HTTP error translation.
- Calling service-layer functions.
- Cache invalidation after successful writes.

Services should do:

- Business rules and reusable state transitions.
- DB queries and updates using passed `AsyncSession` or explicit session factories when background work requires it.
- Filesystem/storage side effects through `lab.storage` and directory helpers.
- Concurrency/race handling, quota/service invariants, and reusable helpers.

Evidence-backed patterns:

- Team routes delegate almost all member/invite/logo/secret behavior to `team_service` and validate path `team_id` against the dependency result.
- Experiment routes combine permission dependencies, filesystem-backed experiment service calls, and small response shaping.
- Task routes parse/validate `task.yaml`, resolve providers, handle upload/file path safety, then delegate persisted metadata and file writes to `task_service`.
- `experiment_access_service` is a compact service-only example: upsert/update, concurrency race handling via `IntegrityError`, and query helpers.

## Schemas and task YAML validation

Use Pydantic models in `api/transformerlab/schemas/` for distinct request/response contracts. Pydantic v2 is in use.

`TaskYamlSpec` is the canonical model for task YAML. It forbids unknown top-level fields and requires:

- `name`
- `run`

Supported optional fields include:

- `resources`: `compute_provider`, `cpus`, `memory`, `disk_space`, `accelerators`, `num_nodes`, `fleet_name`, `instance_type`, `cloud`, `region`, `zone`, `use_spot`, `image_id`
- `envs`
- `setup`
- `github_repo_url`, `github_repo_dir`, `github_repo_branch`
- `parameters`
- `sweeps`: `sweep_config`, `sweep_metric`, `lower_is_better`
- `minutes_requested`

Task YAML parsing supports an older wrapper shape with a root `task:` key, then validates the inner object. The router maps the validated model into the internal flat task metadata shape:

- `resources.compute_provider` becomes provider name and may be resolved to provider ID/name.
- CPU/memory/disk/accelerator/node values become flat task fields.
- `envs` becomes `env_vars`.
- sweeps become `run_sweeps`, `sweep_config`, `sweep_metric`, and `lower_is_better`.

## Filesystem storage bias

Prefer filesystem-backed state when it needs to be visible to distributed workers or synchronized through team workspace storage. Use the storage abstraction, not raw local filesystem calls, for workspace data:

- `lab.storage` for open/copy/list/remove/makedirs operations.
- `lab.dirs` helpers for current team/organization workspace paths.
- Secure filenames and block traversal for route-supplied path segments.

Tasks and jobs are heavily filesystem-backed. The DB stores auth, teams, providers, quotas, queue metadata, permissions, share links, and similar control-plane state.

## SQLAlchemy, Alembic, and timestamps

DB rules:

- Use async SQLAlchemy sessions from `get_async_session()` in routes and passed `AsyncSession` objects in services.
- Default DB can be SQLite; PostgreSQL is selected by DB environment configuration. Avoid dialect-specific SQL in normal service code.
- The session module uses `NullPool` for SQLite and under pytest; PostgreSQL production can use a configured async pool.
- Runtime DB initialization runs Alembic migrations; do not rely on ad-hoc `create_all()`.
- Do not add foreign keys in model definitions or Alembic migrations. Use explicit indexed string columns, unique constraints, and service-level integrity checks.
- For migrations, use helper checks such as table/column/index existence to keep upgrades idempotent across SQLite and PostgreSQL.

Timestamp rule:

- SQLAlchemy `DateTime` columns are naive and represent UTC.
- Use `utc_now_naive()` whenever assigning to or comparing against a DB `DateTime` column.
- Do not use `datetime.now()`, `datetime.utcnow()`, or hand-rolled timezone stripping in call sites.

## SDK reinstall gotcha

The backend imports `lab` from the installed SDK package, not directly from `lab-sdk/` source. If a backend fix depends on SDK source changes, reinstall the local SDK package in editable mode and restart the API process before testing the backend behavior.
