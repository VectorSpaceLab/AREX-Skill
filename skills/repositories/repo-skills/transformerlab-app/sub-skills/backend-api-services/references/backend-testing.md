# Backend testing and checks

Use this reference when adding or changing backend routes, services, schemas, DB models/migrations, or auth/team behavior.

## Command map

Run from the repository root unless a command says otherwise.

Setup/start commands:

```bash
cd api && ./install.sh
cd api && ./run.sh
npm run api:install
npm run api:start
```

Backend tests:

```bash
cd api && pytest
cd api && pytest test/<file>::<test>
```

Lint/format Python after backend changes:

```bash
cd api && ruff check
cd api && ruff format <changed-python-files>
```

DB migrations:

```bash
cd api && alembic upgrade head
```

Useful lightweight import check after DB/router refactors:

```bash
cd api && python -c "import transformerlab.routers"
```

If a backend change depends on local SDK source edits, reinstall the local SDK in editable mode and restart the API before testing. The backend imports the installed `lab` package.

## What to test

Prefer fast service-level tests before full API integration tests.

Service-level tests should cover:

- Business rules and error branches.
- DB query/update behavior with mocked `AsyncSession` and result objects.
- Race handling, such as insert-vs-update upserts and `IntegrityError` rollbacks.
- Filesystem/storage side effects with `lab.storage` or directory helpers monkeypatched to temporary locations.
- UTC timestamp assignment/comparison using `utc_now_naive()`.
- Provider/team lookup decisions without launching real providers.

Router/API tests should cover:

- Auth and team scoping (`Authorization`, `X-Team-Id`, owner vs member role).
- Request/response schema shape and HTTP status mapping.
- Path traversal and reserved filename protection for file endpoints.
- Cache invalidation and response visibility after writes.
- Permission dependencies for experiment/team routes.

Avoid slow or external dependencies unless the task requires them. Mock S3/cloud providers, GPU/provider launches, filesystem-heavy operations, subprocesses, and network calls.

## Existing test patterns to mirror

- Service tests use `AsyncMock`, `MagicMock`, and monkeypatches to isolate DB/storage behavior.
- Integration tests use a FastAPI `TestClient` fixture that obtains an admin JWT and automatically adds auth/team headers to non-auth requests.
- DB integration tests run Alembic migrations before using the app, matching production startup.
- Task YAML/file tests redirect experiment/workspace directories to temporary paths and assert invalid IDs do not create leaked directories.
- Provider-resolution tests pass fake providers and assert unknown names return HTTP 400 with available provider names.
- Public/anonymous route tests assert auth dependencies are not accidentally added to intentionally public routes.

## Async test notes

- Use `pytest.mark.asyncio` for async service/router helper tests.
- When mocking `AsyncSession.execute`, return an object whose methods match the code path: `scalar_one_or_none()`, `scalars().all()`, `scalar()`, or `rowcount`.
- For service methods that commit or roll back, assert `commit`, `rollback`, and `add` calls explicitly.
- When a service catches `IntegrityError`, simulate it on `commit` and assert rollback.
- Avoid relying on real event-loop connection pools; the backend session layer already uses `NullPool` under pytest.

## Schema and task YAML tests

When testing `task.yaml` behavior:

- Include required fields `name` and `run`.
- Assert unknown fields are rejected because the schema forbids extras.
- Assert the old root `task:` wrapper still parses if touched.
- Assert `resources.compute_provider` is resolved to provider metadata only for non-interactive tasks.
- Assert missing tasks return a task-specific 404, while existing tasks without `task.yaml` return a YAML-specific 404.
- Assert invalid experiment IDs do not create workspace directories as a side effect.

## Auth/team tests

For protected service-backed routes:

- Verify missing/expired auth returns 401 or the expected auth error.
- Verify JWT requests without `X-Team-Id` or team cookie fail.
- Verify non-member team IDs fail with 403.
- Verify member vs owner permissions separately when using `require_team_owner`.
- For routes with a `{team_id}` path parameter, assert a mismatched header/team cookie returns 400.
- For API-key paths, test scoped-key behavior separately from all-team keys when the changed code touches API key auth.

## DB and migration tests

For DB-backed changes:

- Add or update SQLAlchemy models with indexed string columns and unique constraints as needed, but no foreign keys.
- Add Alembic migrations that are safe on SQLite and PostgreSQL.
- Use helper checks for existing tables/columns/indexes when a migration may run against mixed states.
- Run `cd api && alembic upgrade head` after migration edits.
- Prefer service tests that exercise queries through the same helper functions used by routes.
- Test `DateTime` writes with `utc_now_naive()` and assert stored/comparison datetimes are naive UTC values.

## Cache and filesystem tests

When a route writes data that affects cached reads:

- Assert cache invalidation is called with the relevant logical tag/key when feasible.
- Exercise the read path after the write in an integration test if stale cache behavior is likely.
- For workspace files, monkeypatch storage and directory helpers instead of touching a real user workspace.
- Check reserved names such as task metadata files cannot be overwritten through generic upload/edit endpoints.

## Verification hard cases

Use these synthetic cases when this sub-skill is part of repo-skill verification:

1. **Protected service-backed route with schema/test**: add a small endpoint that accepts a Pydantic request, requires `get_user_and_team`, delegates all business logic to a new service helper, writes either team-scoped storage or a DB row, and includes service tests plus an owner/member/header mismatch integration test.
2. **Naive UTC datetime bug fix**: fix a service that compares or writes SQLAlchemy `DateTime`, replace local/aware datetime calls with `utc_now_naive()`, and add a test proving the value is timezone-naive, represents UTC, and works in both update and insert branches.
