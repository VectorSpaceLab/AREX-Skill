# Server troubleshooting

Use this when backend route imports, API calls, migrations, dynamic settings, telemetry ingest, jobs, or insights fail.

## Fast triage commands

Run from a checkout root unless noted.

```bash
# Route registration, import-only; does not create the FastAPI app or run startup.
python <this-sub-skill>/scripts/check_server_routes.py --server-path observal-server --pretty

# API health when a stack is running.
curl http://localhost/health
curl http://localhost/healthz

# Focused backend tests with mocked external services.
pytest tests/test_*routes*.py -q
pytest tests/test_clickhouse_migrations.py tests/test_clickhouse_resource_tuning.py -q
pytest tests/test_migration_api.py tests/test_migration_job_lifecycle.py -q
pytest tests/test_insights_access.py tests/test_insights_agent_lookup.py -q
```

Expected route-helper success in a dependency-complete environment: `ok: true`, `rest_router_count: 37`, expected route prefixes present, and `graphql_prefix: /api/v1/graphql`.

## Install/import failures

| Symptom | Likely owner | What to check | Expected fix |
| --- | --- | --- | --- |
| `ModuleNotFoundError: fastapi`, `sqlalchemy`, `pydantic`, `strawberry`, `authlib`, `onelogin`, `litellm`, or `arq` while importing server routes | Server environment | The server test/runtime environment is not active or dependencies were not installed. | Activate/install the server package environment, then rerun the route helper. Do not treat dependency import failure as route absence. |
| `ModuleNotFoundError: observal_shared` | Server/shared package path | Shared package is not installed or not on `PYTHONPATH`. | Install editable shared package or add `packages/observal-shared` to the test path. The route helper tries this automatically when `--server-path` points inside a repo root. |
| Route helper `ok: false` after deps are installed | Route registration | Read `error_type`, `error`, and traceback when using `--traceback`. | Fix import-time side effects or missing imports. Route modules should not require DB/Redis/ClickHouse connections at import time. |
| `ImportError` from a route package after adding a submodule | Package registration | `api/routes/agent/__init__.py` or `api/routes/admin/__init__.py` may import the new module too early or not at all. | Import the submodule in package `__init__.py` only after shared router definitions are available; avoid circular imports. |

## Missing or wrong routes

| Symptom | Likely cause | Fix | Verification |
| --- | --- | --- | --- |
| New top-level API returns 404 | Router was not imported/appended in `routes.REST_ROUTERS`. | Import `router as <name>_router` in `routes.py` and add it to `REST_ROUTERS`. | Route helper shows count increased or new prefix present; HTTP test reaches handler. |
| New admin/agent package endpoint returns 404 | Submodule decorators never ran. | Import the submodule in `api/routes/admin/__init__.py` or `api/routes/agent/__init__.py`. | Route helper shows same top-level prefix but route count for that router increases. |
| Component version endpoint duplicated or inconsistent | Logic added to one component route instead of shared factory. | Move shared behavior to `component_versions.py`; include tests for multiple component types if behavior is generic. | `tests/test_component_versions_routes.py` passes. |
| GraphQL route affected by REST change | REST and GraphQL registration were mixed. | Keep GraphQL in `include_graphql_routes`; only REST routers go in `REST_ROUTERS`. | Route helper still reports `graphql_prefix: /api/v1/graphql`. |

## Auth and permission failures

| Symptom | Expected meaning | Debug path | Fix |
| --- | --- | --- | --- |
| `401 {"detail": "Missing credentials"}` | No `Authorization: Bearer ...` header reached `get_current_user`. | Check client config and route dependency. | Send a Bearer access token or use `optional_current_user` only for public reads. |
| `401 {"detail": "Invalid or expired token"}` | JWT decode failed, token expired, user missing, or revoked token. | Check JWT keys, access-token expiry, Redis revocation state, and user row. | Re-login/refresh token; restore JWT key volume if it was recreated. |
| `503 Auth service temporarily unavailable` | Redis failed during revocation or must-change-password checks; auth fails closed. | Check Redis health and `REDIS_URL`. | Restore Redis; do not bypass revocation checks in route code. |
| `403 Password authentication is disabled (SSO-only mode)` | `deployment.sso_only` blocks password-based endpoints. | Confirm dynamic setting and endpoint dependencies. | Use OIDC/SAML flow or disable SSO-only after admin validation. |
| `403 Insufficient permissions` | Role gate or object-level permission failed. | Inspect `require_role`, `get_effective_*_permission`, visibility helpers, team membership, and co-author state. | Use existing helpers; do not replace 404 visibility masking with metadata-disclosing 403 on hidden resources. |
| SCIM mutation returns 401 | SCIM token verifier failed, not normal JWT auth. | Check hashed `ScimToken.active` row and bearer token format. | Use the SCIM bearer token, not a user JWT. |

Bearer-token note: some older public endpoint text may mention API keys, but backend route dependencies currently use Bearer JWTs for authenticated HTTP APIs unless a route has its own explicit verifier such as SCIM.

## CLI/API mismatch and config failures

| Symptom | Check | Fix |
| --- | --- | --- |
| CLI says connection failed | `observal config show`; `curl http://localhost/health`; stack `ps`/logs. | Set the CLI `server_url` to the actual API/LB URL and restart unhealthy services. |
| Frontend or CLI points at wrong API | `GET /api/v1/config/endpoints` and `GET /api/v1/config/version`. | Set dynamic `deployment.public_url` and `deployment.frontend_url` consistently. |
| OpenAPI docs are missing | `observability.enable_openapi` dynamic setting. | Enable if this is intentional for dev; production may deliberately disable docs. Restart if marked restart-required. |
| SSO health stale after settings update | OAuth clients are built at startup; some SSO keys are restart-required. | Restart API after changing OAuth/Google/GitHub client settings. SAML dynamic config can also use route-level cache signatures. |
| Setting write returns 409 externally managed | Key is supplied by a `NAME_FILE` secret or is file-only. | Change the mounted secret file, not the admin settings API. |
| Sensitive value appears as redacted | Expected behavior after initial entry. | Use admin write/revoke flows; never log or display plaintext secrets after storage. |

## Optional dependency and insights failures

| Symptom | Likely cause | Fix | Verification |
| --- | --- | --- | --- |
| `402 Insights are not available on this server` | Insights package path/import guard says unavailable. | Install server optional dependencies or restore insights module imports. | `GET /api/v1/insights/status` returns `available: true` or precise missing-setting reason. |
| Insights status says no model configured | `insights.model_sections` is empty. | Set Sections Model in dynamic settings using LiteLLM `provider/model` format. | `tests/test_insights_*` still mock LLM calls and pass. |
| `litellm: call failed` | Bad API key, provider/model format, base URL, AWS/Bedrock credentials, or provider unavailable. | Check `insights.api_key`, `insights.api_base`, `insights.api_version`, model IDs, AWS region; keep tests mocked. | `test_insights_connection` route returns actionable provider diagnostics. |
| SAML route import or runtime errors | Missing `python3-saml`/OneLogin dependency, malformed cert/key, wrong URLs, clock skew. | Validate SAML settings, file-backed SP key/cert pair, frontend URL, cert expiry, and IdP reachability. | `tests/test_sso_saml_routes.py` and `tests/test_admin_sso_routes.py` pass. |
| OIDC/GitHub/Google OAuth error | Missing `authlib`/HTTP dependency or dynamic settings mismatch. | Configure client ID/secret/discovery URL/allowed orgs/domains, restart for OAuth client rebuild. | SSO health checks return pass or targeted fail entries. |

## Telemetry ingest and harness-boundary failures

| Symptom | Server-side meaning | Fix |
| --- | --- | --- |
| `POST /api/v1/ingest/session` returns 422 | Pydantic bounds failed: too many lines, oversized line, bad offsets, missing `hashed_line_count` with `session_hash`, etc. | Fix client payload shape; keep route validators strict. |
| Ingest returns 409 with `session source changed at an acknowledged line` | The same source line index was replayed with different content. | Client/exporter should replay from the repair range or start a new session identity; server should not silently overwrite. |
| Final ingest returns `integrity_ok: false` and `repair_from_line` | Server manifest hash/checkpoint found a mismatch. | Exporter should replay from returned line; server may rewind checkpoint. |
| `GET /api/v1/telemetry/status` returns zero counts | No recent ClickHouse session rows or ClickHouse query failed safely. | Check ingest success, ClickHouse health, and session summaries. Harness hook delivery issues belong to harness-telemetry. |
| Unknown or misclassified harness rows | Session parser/registry issue rather than route issue. | Preserve ingest contract and hand off harness-specific parser/adapter work to harness-telemetry. |
| ClickHouse insert failure during ingest | ClickHouse URL/auth/schema mismatch or migration not applied. | Verify `CLICKHOUSE_URL`, health, `clickhouse_schema_migrations`, and schema columns used by `services.clickhouse.insert`. |

## ClickHouse migration/startup mistakes

| Symptom | Likely cause | Fix | Verification |
| --- | --- | --- | --- |
| Review finds new `CREATE TABLE`/`ALTER TABLE` in `startup.py` | ClickHouse schema change was placed in startup. | Move it to a numbered `clickhouse/migrations/*.sql` file. Startup should not own new ClickHouse DDL. | `pytest tests/test_clickhouse_migrations.py -q`; no new ClickHouse DDL remains in startup. |
| API restarts repeatedly after ClickHouse schema change | Migration was not applied, DDL runs repeatedly, or ClickHouse lacks memory/permissions. | Apply migrations through runner/init service; avoid repeated table rewrites at API startup. | Runner logs pending files then `ClickHouse migrations complete`. |
| Migration runner replays baseline on existing install | Baseline stamping detection failed or baseline tables incomplete. | Check baseline tables: `audit_log`, `layer_snapshots`, `security_events`, `session_events`, `session_stats_agg`, `webhook_deliveries`. | Tests for baseline stamping pass. |
| Query uses a new ClickHouse column but route tests fail | Insert/query helpers or migration/tests not updated together. | Update SQL insert column list, query row parsing, and migration SQL. | Relevant route tests pass with mocked ClickHouse responses containing the new field. |

## PostgreSQL migration failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Alembic autogenerate misses a model | Model not imported in `models/__init__.py` or metadata not loaded. | Import the model in `models/__init__.py`; rerun migration generation/checks. |
| Enum type cannot be dropped | Downgrade order wrong or dependent table still exists. | Drop constraints/tables before enum types; use `checkfirst=True` where adjacent migrations do. |
| Unique conflict returns 500 | `IntegrityError` not caught/rolled back. | Use `commit_or_name_conflict` or route-specific 409 handling with rollback. |
| New column works locally but fresh DB lacks it | Startup `create_all` masked missing migration. | Add Alembic migration and test against migration path. |

## Background jobs and workflow failures

| Symptom | Likely cause | Fix | Verification |
| --- | --- | --- | --- |
| Route enqueue fails | Redis/arq pool unavailable or job not registered in `WorkerSettings.functions`. | Check Redis, `services.redis._get_arq_pool`, and worker registration. | Tests monkeypatch arq pool and assert `enqueue_job` name. |
| Job never runs | Worker not running, cron missing, wrong function name, queue mismatch. | Start arq worker with `worker.WorkerSettings`; ensure job function is in `functions`. | Worker log reports function and cron counts. |
| Migration job stuck queued/running | Worker down or timeout/external boundary stuck. | Check `jobs.migration.run_migration_job`, progress fields, artifact directory permissions, timeouts. | `tests/test_migration_job_lifecycle.py` passes terminal-state cases. |
| Failed export leaves unsafe artifacts | Cleanup guard wrong. | Preserve user-uploaded import/validate artifacts; cleanup only export artifacts created by the job when safe. | Artifact security/lifecycle tests pass. |
| Insights background report fails silently | Job swallowed external exception without setting report status or logs are hidden. | Ensure `run_single_report` handles status transitions and job logs with visible positional Loguru messages. | Insights job/service tests assert failure behavior with mocked LLM. |

## Safe expected signals before handoff

- Route helper import succeeds in the prepared environment and expected prefixes are present.
- Focused route tests pass for changed API family, including auth failure and role/object permission cases.
- PostgreSQL changes have Alembic revisions; ClickHouse changes have SQL migrations; neither relies on startup schema side effects.
- Dynamic setting changes invalidate cache, preserve external-file restrictions, redact sensitive values, and mark restart-pending where required.
- Jobs are registered/enqueued by name and external dependencies are mocked in tests.
- Telemetry/insights changes degrade safely when ClickHouse, Redis, provider APIs, or optional dependencies are unavailable.
