# Migrations, dynamic settings, and background jobs

Use this reference for backend data-shape changes, runtime settings, and arq jobs.

## Storage sources of truth

| Concern | Source of truth | Runtime helpers | Never do |
| --- | --- | --- | --- |
| PostgreSQL schema | `observal-server/alembic/versions/*.py` plus ORM in `models/*.py` | `database.async_session`, `api.deps.get_db`, SQLAlchemy async | Do not rely on startup `Base.metadata.create_all` or legacy `ensure_columns` for new schema. |
| ClickHouse schema | `observal-server/clickhouse/migrations/*.sql` | `services.clickhouse.migrations.run_clickhouse_migrations`, `services.clickhouse.client._query`, `services.clickhouse.insert/query` | Do not add new ClickHouse `CREATE`, `ALTER`, `DROP`, or table rewrites to startup code. |
| Runtime-tunable settings | `enterprise_config` rows via `services.dynamic_settings` | `get`, `get_int`, `get_bool`, sync cache variants, admin settings routes | Do not read runtime settings directly from env vars. |
| Boot-time infrastructure/crypto | `config.Settings` env and `NAME_FILE` secrets | `config.settings`, `observal_shared.secrets.resolve_secret` | Do not move pool URLs, JWT key paths, or crypto boot settings into request-time DB reads. |

## PostgreSQL migration workflow

Use PostgreSQL/Alembic for registry metadata, users, auth config rows, jobs, teams, feedback, alerts, insights metadata, and other relational state.

1. Update or add the SQLAlchemy model in `models/`.
2. Import the model in `models/__init__.py` so `Base.metadata` and Alembic know it exists.
3. Add an Alembic revision under `alembic/versions/`. The project uses descriptive filenames; current revisions include examples such as `014_migration_jobs.py` and `025_team_visibility_review.py`.
4. In `upgrade()`, create tables, columns, enum types, indexes, and foreign keys explicitly. In `downgrade()`, drop in reverse dependency order.
5. If a route writes the new table, add route-level tests plus at least one direct migration/model test when the schema has constraints, enums, or security semantics.
6. Do not add new schema to `startup.ensure_columns`. That function exists as a legacy compatibility guard, not as a migration mechanism.

Expected verification commands:

```bash
pytest tests/test_migration_api.py tests/test_migration_job_lifecycle.py -q
pytest tests/test_admin_users_routes.py tests/test_enterprise_settings_routes.py -q
```

Expected signals: migration-job tables and routes still serialize typed schema values, upload/download artifact gates still enforce auth, and admin settings route tests still pass.

## ClickHouse migration workflow

Use ClickHouse migrations for telemetry, audit, security-event, layer snapshot, session checkpoint, session summary, webhook delivery, and other analytical/time-series tables.

Important runtime evidence:

- Migration files live in `clickhouse/migrations/*.sql` and are executed by `services.clickhouse.migrations`.
- The runner creates `clickhouse_schema_migrations`, records each file stem as its version, strips SPDX/comment lines, splits semicolon-delimited SQL while preserving quoted semicolons, and skips already-applied versions.
- Existing installations with all baseline tables can have `001_baseline.sql` stamped as applied instead of replayed.
- `services.clickhouse.schema.init_clickhouse()` is for runtime settings, materialization checks, resource tuning, and TTL application after schema exists. It is not the place for new table/column DDL.

Add a ClickHouse schema change this way:

1. Create the next numbered SQL file in `clickhouse/migrations/`, for example `005_<short_name>.sql`.
2. Put all ClickHouse DDL and data backfill SQL in that file. Use `IF EXISTS` or `IF NOT EXISTS` where idempotency is intended.
3. If changing `session_events`, `session_stats_agg`, or materialized views, account for the table engine (`ReplacingMergeTree` or aggregate-style table), `FINAL` query needs, projections/indexes, and replay/idempotency behavior.
4. Update `services.clickhouse.insert.py` and `services.clickhouse.query.py` only for runtime reads/writes against the new shape.
5. Update tests for the runner, resource tuning, retention, and any route/service that reads the changed fields.
6. Run the migration runner in a dependency-complete server environment:

```bash
cd observal-server
python -m services.clickhouse.migrations
```

Expected success signal: log lines for each pending migration and a final `ClickHouse migrations complete`. On a test fake, `tests/test_clickhouse_migrations.py` should show applied files skipped and new files recorded.

Focused test commands:

```bash
pytest tests/test_clickhouse_migrations.py -q
pytest tests/test_clickhouse_resource_tuning.py tests/test_clickhouse_retention.py -q
pytest tests/test_layer_snapshot_routes.py -q
```

Expected signals: `_split_sql` preserves quoted semicolons, `run_clickhouse_migrations` records `clickhouse_schema_migrations`, resource overrides become ClickHouse query parameters without breaking `param_*` placeholders, and route tests mock ClickHouse failures safely.

## Repair workflow: ClickHouse DDL was accidentally added to startup

If review finds `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`, table rewrites, or materialized-view DDL newly added to `startup.py` or `services/clickhouse/schema.py`:

1. Remove the schema DDL from startup/runtime initialization.
2. Create a numbered SQL migration under `clickhouse/migrations/` with the same DDL/backfill.
3. Keep only safe runtime behavior in `services.clickhouse.schema`, such as resource settings, TTL tuning, and guarded materialization of existing projections/indexes.
4. Add or update `tests/test_clickhouse_migrations.py` to prove the migration runner applies or skips the file correctly.
5. Add a route/service test for any API behavior that depends on the new column/table.
6. Run the route helper and focused tests. Expected signal: route count unchanged unless a route was also added, migration tests pass, and no new startup DDL remains.

## Dynamic settings workflow

Runtime settings live in the `enterprise_config` table and are accessed through `services.dynamic_settings`.

Use these APIs:

- Async request-time reads: `await ds.get("key")`, `await ds.get_int("key")`, `await ds.get_bool("key")`.
- Sync startup/module-level reads when needed: `ds.get_sync("key")`, `ds.get_sync_int("key")`, `ds.get_sync_bool("key")` after sync cache load.
- Cache management after writes: `await ds.invalidate(key)` and `await ds.refresh_sync_cache()` where adjacent settings routes do.

Key categories currently include:

- Insights: `insights.api_key`, `insights.api_base`, `insights.api_version`, `insights.model_sections`, `insights.model_synthesis`, `insights.model_facets`, batch and registry-match settings.
- Auth/SSO: `auth.self_registration_enabled`, `deployment.sso_only`, `oauth.*`, `google.*`, `github.*`, `saml.*`, JWT expiry settings.
- Deployment/security: `deployment.frontend_url`, `deployment.public_url`, `deployment.cors_origins`, `security.rate_limit_auth`, `security.trace_privacy`, `security.trusted_proxy_ips`.
- Resources/data: `resource.*`, `data.retention_days`, `retention.*`, `inbox.retention_days`, `data.cache_ttl_*`.
- Observability/misc: `observability.log_level`, `observability.log_format`, `observability.enable_openapi`, `observability.enable_metrics`, `misc.harness_allowlist`, `misc.default_harness`.

Sensitive keys are encrypted at rest and redacted from later responses. Current examples: `insights.api_key`, OAuth/Google/GitHub client secrets, SAML IdP cert, SAML SP private key, and SAML SP key password.

Settings route write checklist:

1. Reject file-only or externally managed keys when the existing settings route does.
2. Normalize copy-paste whitespace where adjacent code does, but preserve interior PEM content.
3. Encrypt sensitive values before storage.
4. Mark restart-pending for keys in `RESTART_REQUIRED_KEYS`.
5. Commit the `EnterpriseConfig` mutation.
6. Invalidate dynamic-settings cache and refresh sync cache if the setting is read synchronously.
7. Emit a `SETTING_CHANGED` security event for privileged changes.
8. Return redacted values for sensitive settings except for the deliberate single entry response.

Expected verification commands:

```bash
pytest tests/test_enterprise_settings_routes.py -q
pytest tests/test_admin_sso_routes.py -q
pytest tests/test_clickhouse_resource_tuning.py -q
```

Expected signals: externally managed settings return 409 on write/delete/revoke, sensitive values are redacted, restart-pending keys are tracked, insight API key update removes legacy credential rows, and resource values propagate into ClickHouse query settings.

## Boot-time config workflow

`config.Settings` owns infrastructure and crypto settings required before the DB/cache is available:

- `DATABASE_URL`, `CLICKHOUSE_URL`, `REDIS_URL` and pool/timeout knobs.
- `SECRET_KEY`, `OLD_SECRET_KEY`, `JWT_SIGNING_ALGORITHM`, `JWT_KEY_DIR`, `JWT_KEY_PASSWORD`.
- `GIT_CLONE_TOKEN`, logging, `SKIP_DDL_ON_STARTUP`, demo-account bootstrap settings.
- `NAME_FILE` secret resolution through `observal_shared.secrets.resolve_secret`.

Only add to `config.py` when the setting must be available before dynamic settings and the database cache are loaded. Otherwise add a dynamic setting.

## arq jobs workflow

Job owners:

- `jobs/catalog.py`: insights report generation, weekly discovery, user-profile refresh.
- `jobs/maintenance.py`: component-source sync, ClickHouse OPTIMIZE/part-health checks, inbox cleanup.
- `jobs/migration.py`: export/import/validate migration jobs and artifact cleanup.
- `services/alert_evaluator.py`: alert evaluation cron.
- `worker.py`: arq function registration, cron schedules, worker startup/shutdown, Redis settings.

Add or change a job this way:

1. Implement the async function with signature `async def job_name(ctx: dict, ...)`.
2. Register it in `WorkerSettings.functions` if it can be enqueued.
3. Add a `cron(...)` entry only for scheduled jobs, with `timeout` and `unique=True` where duplication would be dangerous.
4. Use `services.redis._get_arq_pool()` from routes/services to enqueue by registered function name.
5. Load dynamic settings in the job at runtime, not at import time, unless it is a worker startup configuration.
6. Tests should monkeypatch external boundaries (`async_session`, ClickHouse `_query`, object storage, arq pool, timeouts, LLM calls) and assert terminal status/audit behavior.

Focused tests:

```bash
pytest tests/test_migration_job_lifecycle.py tests/test_migration_api.py -q
pytest tests/test_insights_self_learn_reuse.py tests/test_insights_access.py -q
```

Expected signals: migration jobs update DB progress, handle timeouts/errors, clean artifacts only when safe, emit security events, and insight jobs do not make real LLM calls.
