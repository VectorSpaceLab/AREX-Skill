# Backend Troubleshooting

Use this matrix to diagnose common backend failures without exposing secrets or running destructive utilities by default.

## PostgreSQL and migrations

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| App container exits during startup at migration step | Database unavailable, wrong DB env, migration error | `docker compose logs -f db app`; verify `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` in backend env | Wait for DB health, correct env, then `make migrate`. For migration errors, inspect generated migration and rollback only on disposable/dev DB or with operator approval. |
| `psycopg.OperationalError` in app/tests | PostgreSQL not running or testcontainers cannot start | For app: `docker compose ps db`; for tests: confirm Docker daemon or set `TEST_DATABASE_URL` | Start Docker, use compose DB, or provide disposable test DB URL. |
| Tests fail while creating tables with missing FK targets | New model not imported in model registry or tests import order changed | Ensure the model is included in the app model package import path before `BaseDbModel.metadata.create_all()` in tests | Add the model to the model package exports/registry and create a migration. |
| Alembic autogenerate omits indexes/constraints | Partial indexes, custom constraints, enum-like strings, or server defaults need manual migration code | Compare model change with migration diff | Hand-edit migration for partial indexes, unique constraints, data backfills, nullable transitions, and downgrade behavior. |
| `reset_db`/data migration script looks tempting for a failing test | Destructive helper is being used as a shortcut | Check whether a targeted migration or fixture rollback solves it | Do not run reset/destructive scripts unless the DB is explicitly disposable. Prefer pytest transaction rollback and targeted fixture fixes. |

Startup sequence is significant: ensure Svix DB, apply migrations, initialize provider settings, priorities, admin developer, series types, legacy idempotent data fixes, archival settings, webhook event types, then start FastAPI.

## Redis, Celery, and testcontainers

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| Pytest hangs or fails before tests run | Testcontainers cannot pull/start PostgreSQL or Redis | Confirm Docker daemon and container permissions; set `TEST_DATABASE_URL` / `TEST_REDIS_URL` for disposable external services | Start Docker, set explicit test service URLs, or run a narrower unit test that mocks Redis/Celery. |
| Sync status endpoints return empty or SSE never updates | Redis is missing, using different Redis DB, or emit failed best-effort | `docker compose logs -f redis app`; check Redis host/port/db in backend env | Fix Redis env and restart app/worker. Remember events have a 24h TTL and recent list caps at 200. |
| Background sync/webhook task never executes | Celery worker not running, queue mismatch, Redis broker issue | `docker compose logs -f celery-worker redis`; verify worker command includes `default,sdk_sync,garmin_sync,webhook_sync` | Start/restart worker; check broker URL derived from Redis settings. |
| Dashboard stats stale | Data-point total is cached/estimated and refresh dispatch is mocked in tests | Check dashboard cache task logs | Trigger refresh task in a running dev stack or accept approximate cold-cache values. |
| Linked-account sync does duplicate pulls | Redis primary lock expired, provider account lacks `provider_user_id`, or fan-out flags changed | Inspect sync-status `source` and metadata; check active connections share provider user id | Preserve `linked_sync:` key semantics and 4h TTL; secondary tasks should emit `linked_account` status and avoid provider API calls. |

## Svix and outgoing webhooks

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| `/api/v1/webhooks/endpoints` returns 503 | Outgoing webhooks disabled or no Svix client | `GET /api/v1/config`; check `OUTGOING_WEBHOOKS_ENABLED` and Svix env | Enable outgoing webhooks in backend env and configure Svix URL/JWT/auth token for the environment. |
| Startup logs say Svix unreachable during event-type sync | Svix server is still booting or URL is wrong | `docker compose logs -f svix-server app` | Usually safe: registration is idempotent and retries next boot. Fix URL/health if persistent. |
| Endpoint scoped to one user receives no events | Svix channels were patched incorrectly | Inspect endpoint channels through the webhook endpoint response | Use user scope as `user.<uuid>`. To clear scope, patch with `user_id: null`; do not set an empty channel list as a substitute. |
| Timeseries webhook duplicates or rejects event ids | Idempotency key contains unsupported characters or same batch retried | Check event helper uses sanitized `_safe_key` for timestamps | Keep event ids limited to Svix-safe characters and treat 409 duplicate as success. |
| Ingestion fails because webhook delivery fails | Delivery exceptions propagated from helper | Event helpers should enqueue best-effort and log only | Do not let Svix HTTP failures block data ingestion. Preserve best-effort behavior. |

Outgoing webhook management is an external API family; if endpoint paths change, update `docs/docs.json` API Reference navigation.

## AWS, raw payloads, and Apple XML import

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| Import inspection or app startup warns about missing AWS credentials | Raw payload/FIT/S3 config optional but boto3 may report absent credentials | Check whether `RAW_PAYLOAD_STORAGE=s3`, Apple XML S3 import, SNS verification, or FIT storage is actually enabled | If not using S3/SNS, warnings are expected and not a backend block. If using them, set AWS bucket, region, access credentials, SNS topic, and raw payload S3 settings. |
| Presigned URL endpoint fails | AWS bucket/client config missing or wrong | Check backend env and app logs, never print secret values | Configure bucket/region/access keys or use direct upload in local tests. |
| SNS notification rejected | Topic ARN/signature or AWS config mismatch | Check `AWS_SNS_TOPIC_ARN` and environment; confirm provider route is intended system endpoint | Fix SNS config; keep network/live AWS checks out of default tests. |
| Raw payload replay script requires credentials | It is credential/network/S3/API-bound | N/A | Treat replay as a maintenance utility only. Do not bundle/run as a default verification step. |

## Auth, tokens, API keys, and applications

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| Login returns 401 for missing form fields | FastAPI validation on `/auth/login` is normalized to generic credentials error | Verify request uses `application/x-www-form-urlencoded` with `username` and `password` | Send OAuth2 password form data; do not rely on JSON body. |
| External endpoint returns `Authentication required: provide JWT token or API key` | Missing credentials | Check headers | Send either `Authorization: Bearer <developer-jwt>` or `X-Open-Wearables-API-Key: <api-key>` for `ApiKeyDep` endpoints. |
| External endpoint returns `Invalid or missing API key` | Header present but key not in DB | Check API key was created in current database | Create a new API key in the developer portal or with developer JWT. |
| Developer endpoint rejects SDK token | SDK-scoped token cannot access developer-only routes | Decode only in a safe local test if needed; inspect token source | Use developer login/refresh token for admin routes. SDK token is only for SDK endpoints. |
| App secret cannot be retrieved | Secret is intentionally one-time | Check application response on create/rotate | Rotate secret and store the new plain value securely. |
| Refresh works once then old token fails | Refresh token rotation is expected | Check `refresh_token` response contains a new refresh token | Persist the new refresh token after every refresh. |
| Password update appears not to work in tests | bcrypt is patched in tests for speed, or wrong module path was patched | Inspect test fixtures and auth helper | Use the native test helpers; do not assert production bcrypt timings in unit tests. |

## Dates, pagination, and data correctness

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| Query misses records on the end date | Repository uses half-open interval and date-only midnight end has special expansion only in timeseries repository | Check whether the endpoint uses `parse_query_datetime` and whether end date is a whole-day date | Pass explicit exclusive end timestamp or update service consistently if endpoint should include whole day. |
| Timeseries pages repeat or skip records | Cursor direction or `(recorded_at, id)` keyset ordering mishandled | Compare `next_cursor`/`previous_cursor` use and sort direction | Use returned cursors verbatim; preserve tuple keyset comparisons. |
| Activity summary double-counts provider daily totals | `is_daily_total` semantics changed or provider emits both daily total and samples | Check `is_daily_total` for affected series rows | Aggregation should prefer daily-total rows when any exist, otherwise sum samples. Update ingestion/provider code accordingly. |
| Body summary blood pressure missing despite two readings | Systolic/diastolic timestamps differ by more than 5 seconds | Compare recorded timestamps | Write paired blood pressure samples with aligned timestamps or adjust tolerance intentionally with tests. |
| Sleep summary date looks like wake-up date | Sleep summaries aggregate by sleep/wake local date, not always start date | Inspect `zone_offset`, start/end datetimes, and nap flags | Preserve wake-up/local-date behavior unless changing public API semantics and docs/tests. |
| Events delete wrong resource type returns 404 | Category guard is working | Verify id/category pairing | Use category-specific delete endpoints and service category guard. |

## OpenAPI and docs navigation

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| Docs API Reference missing a new endpoint | `docs/docs.json` not updated for `External: *` route | Run checker with `--import-openapi`; inspect reported missing endpoint pages | Add exact `METHOD /api/v1/...` string under the appropriate API Reference group. |
| OpenAPI duplicate operation-id warning | Route function names collide across deprecated compatibility paths | Optional OpenAPI import warning output | Known warnings currently affect deprecated Oura webhook compatibility endpoints. If touching them, use unique function names or explicit operation ids. |
| External endpoint appears under wrong docs group | Incorrect route tag or docs navigation placement | Check v1 router tag and docs group | Keep route tag and docs group semantically aligned. |
| Frontend/MCP caller fails after endpoint rename | Caller constants/client not updated | Search portal and MCP service layers | Coordinate with [frontend-portal](../../frontend-portal/SKILL.md) or [mcp-server](../../mcp-server/SKILL.md). |

## Configuration and environment

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| App import fails with missing `SECRET_KEY` | Required auth setting absent | Check backend config env file and process env | Set `SECRET_KEY` for any real run. The bundled checker supplies a harmless fallback only for optional import inspection. |
| Redis URL malformed with special characters | Username/password not URL-encoded or wrong TLS flag | Run config utility tests or inspect computed URL in safe local debug | Use `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_SSL`; settings builder URL-encodes credentials. |
| CORS blocked in browser | `CORS_ORIGINS` excludes frontend or allow-all disabled | Check backend env and frontend origin | Add frontend URL to `CORS_ORIGINS` or enable `CORS_ALLOW_ALL` only for local/dev. |
| Access logs flood with client errors | 4xx response body logging enabled with high cap | Check access-log settings | Keep `LOG_ERROR_RESPONSE_BODY` disabled unless actively debugging; respect max bytes/per-minute caps. |
| OAuth redirect uses wrong host | Legacy provider redirect URI overrides `API_BASE_URL` | Check per-provider `*_REDIRECT_URI` env and `API_BASE_URL` | Prefer `API_BASE_URL`; legacy redirect vars emit deprecation warnings. |
| Managed Redis TLS fails | TLS enabled but endpoint/cert assumptions wrong | Check `REDIS_SSL=true` and `rediss://` URL | For TLS Redis, ensure the server presents a valid cert because settings require cert verification. |

## Backend test failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Tests try real HTTP/provider/AWS calls | A global mock path no longer matches after refactor | Update `tests/conftest.py` patches and focused tests so provider/AWS/httpx interactions are mocked. |
| Webhook tests hang on Celery/Redis | Dispatch mock not applied at the import path used by code | Patch the exact task object imported by the helper; preserve autouse `mock_webhook_dispatch`. |
| Factory-created rows violate unique constraints across tests | Factory session or unique fields not isolated | Ensure factory session autouse fixture is active and per-test transactions roll back; use unique Faker values. |
| Pydantic response validation fails for old data | ORM row has invalid email/enum/null | Existing user list skips invalid emails; for new fields add safe migration/backfill or tolerant response logic with tests. |
| `ruff` fails annotations/imports | Backend lint requires annotations and sorted imports | Add type hints to every function and run `uv run ruff check . --fix && uv run ruff format .`. |

## Safe escalation order

1. Run the bundled static checker.
2. Read the closest reference in this sub-skill.
3. Reproduce with the narrowest route/service/repository test file.
4. Check Docker logs only for the affected service.
5. Expand to related integration/task tests.
6. Only then run broader backend checks (`ruff`, `ty`, full pytest) if the change scope justifies it.
7. Avoid destructive scripts, real credentials, real provider calls, real AWS/Svix targets, or production databases unless the user explicitly authorizes that operational task.
