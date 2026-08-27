# Backend troubleshooting

Use this when backend behavior fails before you decide whether to edit routers, services, schemas, DB code, or tests.

## Missing API dependencies or wrong runtime context

Symptoms:

- `ModuleNotFoundError` for FastAPI, SQLAlchemy, `transformerlab`, or `lab`.
- API starts from the wrong directory and cannot import `api:app`.
- Import checks pass in one shell but uvicorn fails in another.

Actions:

1. Activate the configured Python environment for the project.
2. Reinstall backend dependencies if needed:

   ```bash
   cd api && ./install.sh
   ```

3. Run backend commands from `api/` when importing source modules:

   ```bash
   cd api && python -c "import transformerlab.routers"
   ```

4. Start the API with:

   ```bash
   cd api && ./run.sh
   ```

5. Remember that `api/api.py` is a standalone source entry point and `transformerlab.api` is not the import target.
6. If a fix touched SDK source used by the backend, reinstall the local SDK package and restart the API.

## Auth 401, 403, or missing team context

Symptoms:

- `401 Authentication required`.
- `400 X-Team-Id header or team cookie required for JWT authentication`.
- `403 User is not a member of the specified team`.
- Owner-only endpoints fail for a member.
- Files unexpectedly resolve under the wrong team workspace.

Actions:

1. Confirm the request carries a valid Bearer JWT or auth cookie.
2. For JWT requests, send `X-Team-Id` or a valid team cookie.
3. Fetch the user's teams first when unsure which team ID to use.
4. For API-key requests, check whether the key is scoped to one team or can act across teams.
5. For routes with `{team_id}`, compare the path parameter to `get_user_and_team()["team_id"]`; mismatches should return 400.
6. For owner-only actions, use `require_team_owner` and test owner/member paths separately.
7. For intentionally public endpoints, verify they are not protected by a router-level dependency.

## Context variables not propagating to threads

Symptoms:

- A background callback reads or writes files in the wrong organization workspace.
- Job or task lookups fail with missing directory errors even though the object exists for the active team.
- Behavior only fails in `run_in_executor()` or callbacks scheduled from another thread.

Cause:

- Team/organization directory selection is stored in `contextvars`; it does not automatically cross thread or `run_coroutine_threadsafe()` boundaries.

Actions:

1. Capture the `team_id` before crossing the thread boundary.
2. Inside the executor function or scheduled coroutine, call `lab.dirs.set_organization_id(team_id)` before workspace/storage access.
3. Clear it with `lab.dirs.set_organization_id(None)` in `finally`.
4. Add a test that simulates the callback/executor path if the bug was thread-specific.
5. If the issue is deeper provider launch lifecycle, route to `../task-execution-compute/SKILL.md`.

## Alembic or DB failures

Symptoms:

- Startup fails during DB initialization.
- Migration logs show missing table/column/index or relation errors.
- Tests fail on PostgreSQL but pass on SQLite, or the reverse.
- Datetime comparisons behave differently across environments.

Actions:

1. Run migrations directly:

   ```bash
   cd api && alembic upgrade head
   ```

2. Inspect the migration for dialect-specific SQL; prefer SQLAlchemy constructs and migration utility helpers.
3. Do not add foreign keys. Use indexed string columns, unique constraints, and service-level validation.
4. For new/changed migrations, guard mixed states with table/column/index existence checks.
5. In services, use `get_async_session()` in routes and pass `AsyncSession` into service functions.
6. For `DateTime` columns, replace local/aware datetime calls with `utc_now_naive()`.
7. Under pytest, remember the session layer uses fresh connections to avoid event-loop-bound pooled connection errors.

## Invalid `task.yaml`

Symptoms:

- HTTP 400 with a validation detail naming a field.
- `YAML content is empty or invalid`.
- Unknown compute provider errors.
- A task exists but `task.yaml` reads return a YAML-specific 404.

Actions:

1. Confirm YAML has required root fields `name` and `run`.
2. Use supported optional fields only: `resources`, `envs`, `setup`, GitHub source fields, `parameters`, `sweeps`, and `minutes_requested`.
3. If using `resources.compute_provider`, match the exact team provider name or rely on the team default provider.
4. Remember unknown fields are rejected by the Pydantic schema.
5. The old root `task:` wrapper can parse, but new code should prefer direct root fields.
6. For upload/edit endpoints, check reserved task metadata filenames and path traversal protections before blaming schema parsing.
7. If provider launch behavior after a valid task is the failure, route to `../task-execution-compute/SKILL.md`.

## Filesystem vs DB storage mismatch

Symptoms:

- A route writes DB state but distributed workers cannot see expected files.
- A file appears for one team but not another.
- A test creates workspace directories as a side effect for invalid IDs.

Actions:

1. Decide whether the state is control-plane metadata or workspace data.
2. Use DB tables for auth, teams, providers, quotas, queues, permissions, and share links.
3. Use team-scoped filesystem storage for tasks, jobs, experiment artifacts, secrets, and uploaded/editable files.
4. Use `lab.storage` and directory helpers for workspace data; avoid raw filesystem calls except for explicit temporary extraction/assembly steps.
5. Validate IDs and existence before calling helpers that create directories.
6. In tests, monkeypatch directory helpers to a temporary base and assert invalid paths do not create leaked directories.

## Cache or stale response issues

Symptoms:

- Writes succeed but read endpoints return old task/job/experiment data.
- Terminal job status or task list is stale.
- Behavior differs between nodes or after restart.

Actions:

1. Find the read cache key/tag used by the route or service.
2. Invalidate relevant tags after successful writes.
3. For terminal job data, check whether per-node cache is intentionally populated for long TTL reads.
4. Confirm org/team context is part of cache scoping where applicable.
5. If cache setup itself fails at startup, inspect API lifespan ordering and cache backend configuration.

## Service startup and worker ownership

Symptoms:

- Background workers do not run in one API process.
- Queue/status/notification behavior appears active on one process but idle on another.
- Startup logs show a process is not the leader.

Actions:

1. Check worker-leader logs from API startup.
2. Only the leader starts migration, sweep status, remote status, notification, remote queue, and upload cleanup workers.
3. Non-leader API processes can still serve routes; do not treat missing worker startup as a router failure.
4. For queue/launch semantics beyond the API/service boundary, route to `../task-execution-compute/SKILL.md`.

## Local provider queue ownership surface

Symptoms:

- Local launch status updates do not appear.
- One local launch blocks another.
- A local launch callback fails only when run from the executor thread.

Actions:

1. Confirm whether the failure is API/service wiring or compute launch lifecycle.
2. The local provider queue serializes launch work and restores org context around executor/callback updates.
3. If fixing only backend service context or status-update plumbing, use this sub-skill.
4. If fixing provider cluster launch, job lifecycle, quota-hold release, or remote/local dispatch semantics, route to `../task-execution-compute/SKILL.md`.

## Safe debugging sequence

1. Reproduce with the smallest service or router test possible.
2. Identify route dependency path: auth/team, permission, session, cache, and service call.
3. Check org context before workspace/storage access.
4. Check whether the state belongs in filesystem storage or DB.
5. Run targeted pytest, then ruff on changed Python files.
6. Escalate to full API tests or running server only when route integration or startup behavior is involved.
