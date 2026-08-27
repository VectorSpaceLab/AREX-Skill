# Data Model and Backend Services

Use this reference when changing backend behavior below the route layer. It describes the current layered contract, key ORM models, schema conventions, services, repository patterns, and side effects such as sync status and outgoing webhooks.

## Layer contract

```text
HTTP request
  → route module (`app/api/routes/v1/...`)
  → service singleton (`app/services/...`)
  → repository (`app/repositories/...`)
  → SQLAlchemy model (`app/models/...`)
  → PostgreSQL / Redis / Celery / Svix as needed
```

Rules:

- Routes parse/validate FastAPI inputs, enforce `ApiKeyDep`, `DeveloperDep`, or `SDKAuthDep`, call services, and return schemas.
- Services own business logic, orchestration, side effects, error semantics, sync events, and outgoing webhook dispatch.
- Repositories own database access only. They should receive/return SQLAlchemy models, primitive rows, or typed query result dicts, not API schemas.
- Models define SQL shape with SQLAlchemy 2.0 `Mapped[...]` fields and shared `app.mappings` aliases.
- Schemas define API payloads and service create/update payloads using Pydantic v2.

## Common base classes and aliases

| Component | Role | Important behavior |
| --- | --- | --- |
| `BaseDbModel` | SQLAlchemy declarative base | Adds `created_at` server default, automatic table name, `id_str`, readable `repr`, and type annotation mapping for UUID/date/datetime/provider enums/token enums. |
| `CrudRepository` | Generic DB CRUD base | `create()` commits/refreshes, `get()` filters by `id`, `get_all()` supports simple filters/sort/offset/limit, `update()` dumps Pydantic update excluding `None`, `delete()` commits, `delete_flush()` lets caller own commit. |
| `AppService` | Generic service wrapper | Instantiates the repository class for a model, exposes `create/get/get_all/update/delete`, and supports `raise_404=True` with centralized exception handling. |
| `DbSession` | FastAPI dependency alias | Yields a SQLAlchemy `Session`; rolls back on exception and closes. The app creates a pooled engine with `pool_pre_ping=True`. |
| `AsyncDbSession` | Async session dependency alias | Available for async DB work, but most current backend services use sync SQLAlchemy sessions. |

Mapping aliases include `PrimaryKey[T]`, `Unique[T]`, `Indexed[T]`, `str_10/32/50/64/100/255`, `email`, `numeric_*`, `datetime_tz`, `FKUser`, `FKDeveloper`, `FKDataSource`, `FKUserConnection`, `FKEventRecord`, `FKSeriesTypeDefinition`, `OneToMany[T]`, and `ManyToOne[T]`.

## Key ORM model map

| Model | Table | Purpose and important constraints |
| --- | --- | --- |
| `User` | `user` | Data owner. Fields: UUID id, names, email, deprecated unique `external_user_id`, optional `PersonalRecord`. |
| `PersonalRecord` | `personalrecord` | Static user descriptors: birth date, sex, gender. Used by summary metrics such as age/max HR. |
| `Developer` | `developer` | Portal/admin account with unique email and bcrypt password hash. |
| `ApiKey` | `api_key` | Global API-key credential. Primary key is the actual `sk-...` key string; `created_by` links to developer. |
| `Application` | `application` | SDK app credentials: UUID id, unique `app_id`, bcrypt `app_secret_hash`, name, owner developer, updated timestamp. Plain secrets are never stored. |
| `RefreshToken` | `refresh_token` | Opaque `rt-...` refresh tokens for developer and SDK token rotation; stores token type, user/app or developer id, last used/revoked timestamps. |
| `UserConnection` | `user_connection` | OAuth/provider connection with provider slug, provider user id, username, access/refresh tokens, expiry, scope, status, last sync, updated time. Important indexes cover active token expiry, unique user-provider, status/user, and active provider external id. |
| `ProviderSetting` | `provider_settings` | Provider enabled flag, live sync mode (`pull`/`webhook`/null), provider webhook secret, and data granularity. |
| `ProviderPriority` / `DeviceTypePriority` | priority tables | Lower numeric priority wins. Used by summaries and data-source selection. |
| `DataSource` | `data_source` | Normalized user/provider/device/source identity. Unique identity is `(user_id, provider, coalesce(device_model,''), coalesce(source,''))`. `user_connection_id` is null for one-off imports. Cascades delete provider data. |
| `SeriesTypeDefinition` | `series_type_definition` | Integer id, unique series code, unit. Seeded at startup from enum definitions. |
| `DataPointSeries` | `data_point_series` | Unified time-series sample with data source, recorded timestamp, zone offset, numeric value, series type id, and `is_daily_total`. Unique `(data_source_id, series_type_definition_id, recorded_at)` supports upsert. |
| `DataPointSeriesArchive` | archive table | Daily archived aggregate rows with bucket start, aggregation type, value, and sample count. Used by data lifecycle/summary queries. |
| `EventRecord` | `event_record` | Unified event/session record: data source, category, type, source name, duration, start/end datetime, zone offset. Has one detail row for workout/sleep/menstrual-cycle categories. |
| `WorkoutDetails` | `workoutdetails` | Workout metrics: HR min/max/avg, energy, distance, speed, cadence, power, elevation, segments and zones JSON. |
| `SleepDetails` | `sleepdetails` | Sleep metrics: total/time-in-bed, efficiency, deep/light/REM/awake minutes, nap flag, sleep-stage JSON. |
| `MenstrualCycleDetails` | `menstrualcycledetails` | Cycle phase, length, fertility and pregnancy snapshot data. |
| `HealthScore` | `health_score` | User/provider/category score with recorded time, value, qualifier, components JSON, optional data source, optional linked sleep record. Unique per user/provider/category/time; partial unique index for linked sleep records. |
| `ArchivalSetting` | `archival_settings` | Singleton row `id=1`, archive-after days and delete-after days. |

## Pydantic schema conventions

- Read schemas that return ORM models use `ConfigDict(from_attributes=True)`.
- External create schemas contain only client-supplied fields; internal create schemas add generated UUIDs/timestamps/hashes.
- API query parameter schemas validate bounds and sort allowlists. Examples: `UserQueryParams`, `EventRecordQueryParams`, `TimeSeriesQueryParams`.
- Cursor-paginated data responses use `PaginatedResponse[T]` with `data`, `pagination`, and `metadata`; legacy user listing uses `OldPaginatedResponse[T]`.
- Deprecated fields stay explicit. `external_user_id` is marked deprecated and must not be accepted by data-fetching endpoints as a user identifier.
- Zone offsets are validated through the date utility alias used by event and timeseries schemas.

## Credential and auth services

| Service | Primary responsibilities | Gotchas |
| --- | --- | --- |
| `DeveloperService` | Register developer accounts; hash new/updated passwords; update developer profile fields. | Passwords are never stored in plain text. Tests patch bcrypt for speed. |
| `ApiKeyService` | Generate `sk-` API keys, list, update, rotate, validate `X-Open-Wearables-API-Key`. | API keys are global and currently visible to any authenticated developer in the internal API-key list. Rotation deletes old key and creates a new default-named key. |
| `ApplicationService` | Generate `app_` ids and `secret_` app secrets, hash secrets, validate app credentials, list/delete/rotate app secrets by developer ownership. | Plain app secret is only returned from create/rotate response. Store tests should assert the old secret stops working after rotation. |
| `RefreshTokenService` | Create developer/SDK refresh tokens, rotate on refresh, revoke tokens. | `refresh_token()` revokes the old token before issuing a new one. Invalid/revoked returns 401; revoke missing returns 404. |
| `create_sdk_user_token` | Mint SDK-scoped access tokens for a user/application pair. | SDK-scoped JWTs are rejected by developer-only dependencies and accepted only by SDK auth. |

`ApiKeyDep` accepts either a developer JWT or an API key header. `DeveloperDep` accepts only a developer JWT. `SDKAuthDep` accepts an SDK-scoped bearer token first, then falls back to API key for backward compatibility.

## User, connection, and data-source flow

1. `UserService.create()` wraps external `UserCreate` into `UserCreateInternal` with UUID and timestamp defaults.
2. `UserService.get_users_paginated()` supports page, limit, sort, search, email, and deprecated `external_user_id` filtering; it skips invalid email rows instead of failing the whole list response.
3. Provider OAuth/SDK/import flows create or update `UserConnection` rows with provider slug, provider user id, tokens, status, and last sync timestamp.
4. `UserConnectionService.get_connections_by_user()` feeds the connections endpoint; capability enrichment uses provider strategy capabilities and provider settings.
5. `DataSourceRepository.ensure_data_source()` deduplicates the `(user, provider, device_model, source)` identity, infers device type from model/source, ensures provider priority rows exist, and fills missing connection/software/source metadata when safe.
6. `DataSourceRepository.delete_user_provider_data()` deletes a user's provider-scoped data by first removing unlinked `HealthScore` rows, then deleting `DataSource` rows and relying on cascade for events/timeseries/details/archive rows.

## Timeseries write and read flow

- Write schemas include user id, source, device model, optional existing data source id, recorded timestamp, zone offset, value, series type, provider, connection id, software version, external id, and `is_daily_total`.
- `TimeSeriesService.bulk_create_samples()` delegates batch resolution/upsert to `DataPointSeriesRepository.bulk_create()` and returns a `WriteCounts` int subclass with `.inserted` and `.updated` counts.
- `DataPointSeriesRepository.bulk_create()` groups creators by inferred provider, batch-ensures data sources, deduplicates conflicting rows inside the batch, chunks insert statements under PostgreSQL's 65,535 bind-parameter limit, and uses `ON CONFLICT DO UPDATE RETURNING (xmax = 0)` to split inserted vs updated counts.
- The unique key is `(data_source_id, series_type_definition_id, recorded_at)`. For pure upsert changes, do not emit business semantics that imply a new sample unless `inserted > 0` matters.
- `get_timeseries()` joins `DataPointSeries` to `DataSource`, filters by user, optional types, source/device, start/end, and returns keyset-paginated raw samples ordered by `(recorded_at, id)`.
- Date filtering is half-open in repositories: `recorded_at >= start` and `< end`. If an end date has midnight time, it is expanded by one day to include the whole date.
- Time-series service emits outgoing webhooks after commit when Svix is enabled. It groups by `(user_id, provider, series_type)` and emits both group and granular events where configured.

## Event record flow

- `EventRecordRepository` resolves or creates `DataSource` rows before creating events.
- Single creates catch duplicate `IntegrityError` and return the existing row when `(data_source_id, start_datetime, end_datetime)` already exists.
- `create_and_flush()` uses a nested savepoint so one duplicate does not poison an outer batch transaction.
- Batch creates group by provider, batch-ensure data sources, chunk rows, and insert with conflict handling.
- `EventRecordService.create_detail()` writes category-specific detail records and then emits the corresponding outgoing webhook if the event and data source can be fetched.
- Sleep creation can merge adjacent sessions within a threshold, recompute sleep scores for affected local dates, and emit sleep-created webhook payloads.
- Deleting workout/sleep/menstrual-cycle events should use `delete_event_record()` with the expected category so wrong-category ids return not found rather than deleting unrelated data.

## Summaries and priority selection

`SummariesService` is the main aggregator for user-facing summaries:

- Sleep summaries aggregate `EventRecord` sleep sessions, details, and physiological time-series. Dates are wake-up/local-date oriented and include nap breakdowns.
- Recovery summaries read `HealthScore` recovery rows and components such as resting HR, HRV RMSSD, SpO2, and recovery score.
- Activity summaries aggregate steps, energy, basal energy, HR stats, distance, flights, and active time from live and archived time-series rows, plus workout-derived elevation. It prefers provider-reported `active_time` daily totals before falling back to a steps-per-minute threshold.
- HR intensity minutes use max HR from `PersonalRecord.birth_date` (`220 - age`) or default 190 when age is unavailable.
- Body summary groups data into `slow_changing` latest values, `averaged` recent vitals, and `latest` point-in-time readings. Blood pressure is only valid when systolic/diastolic timestamps are within a 5-second tolerance.
- `_filter_by_priority()` groups daily results and chooses the lowest provider priority, then lowest device-type priority, then device-name tie-breaker. If you add a summary source, check priority behavior.

## Sync status and linked accounts

Sync status is Redis-backed and best-effort: failures are logged but do not abort sync flows.

| Function/family | Behavior |
| --- | --- |
| `new_run_id(prefix)` | Produces `prefix_<16 hex>` ids. Pull tasks use `pull`, one-shot webhooks use `wh`. |
| `emit(event)` | Logs structured status, stores recent event list, stores latest run event, publishes user/global pubsub, and dispatches terminal outgoing webhooks on a daemon thread. |
| `started/progress/completed/failed/cancelled` | Convenience constructors for common state transitions. |
| `webhook_delivered` | One-shot terminal status for provider webhook processing. |
| `stream_user_events` | SSE generator. Subscribes before replay to avoid missing events; emits heartbeat comments every ~15 seconds. |
| `get_recent_events` | Reads newest-first recent events from Redis, capped at 200. |
| `get_run_summaries` | Builds per-run summaries from run keys and recent started timestamps. |
| `get_all_run_summaries` | Scans all user run keys and supports optional user/provider/status/source filters. |

Linked-account sync uses Redis keys under `linked_sync:` with a 4-hour TTL. Pull/backfill primary election prevents duplicate provider API calls when multiple OW users share a provider account. Secondary profiles receive `source=linked_account` status with `primary_user_id`.

## Seed data service

The seed data generator is developer-scoped and Celery-dispatched from `POST /api/v1/settings/seed`.

- `SeedDataRequest`: `num_users` 1-10, profile config, optional random seed.
- Presets include `active_athlete`, `boxer_footballer`, `sleep_deprived`, `weekend_catchup`, `irregular_sleeper`, `activity_only`, `sleep_only`, `minimal`, and `comprehensive`.
- Generated user first names include `[SEED:<seed>|<preset>]` for reproducibility. Identity fields remain unseeded so repeated runs avoid unique collisions.
- Data is anchored to 2025-01-01 unless explicit date ranges are provided.
- Service creates users, personal records, provider connections, workouts, sleep, workout-bound samples, continuous samples, and health scores, then commits per user.
- Treat the native `make seed` workflow as a dev/disposable database mutation, not a safe verification command for production.

## Outgoing webhooks with Svix

Outgoing webhooks are disabled unless `OUTGOING_WEBHOOKS_ENABLED=true` and Svix auth can be resolved.

- Startup/lifespan calls `register_event_types()`. The function is idempotent and tolerates Svix startup lag by logging and retrying next boot.
- A fixed Svix org id is used. Developer UUIDs double as Svix application UIDs.
- Endpoint management uses Svix endpoint APIs. Endpoint channel filters are `user.<uuid>` when the endpoint is scoped to a user; endpoints without a user channel receive all user-tagged messages.
- Patch semantics matter: omit a key to leave it unchanged; pass `channels=null` only when intentionally clearing the user filter.
- Event helper functions dispatch Celery tasks only when Svix is enabled; missing broker/Svix should not block ingestion.
- Timeseries batches larger than 2,500 samples are chunked; each chunk keeps the full `sample_count` and adds `chunk_index` / `total_chunks`.
- Event ids must be Svix-safe; helper code sanitizes timestamps and other characters to `[a-zA-Z0-9-_.]`.
- Important emitted event groups: `connection.created`, `connection.revoked`, `sync.started`, `sync.completed`, `sync.failed`, `workout.created`, `sleep.created`, `menstrual_cycle.created`, group time-series events such as `heart_rate.created`, plus granular `series.<series_type>.created` events.

## Configuration surfaces

Backend settings are Pydantic settings loaded from the backend config env file plus environment variables. Important groups:

- Core/API: environment, API name/port/version, CORS, paging, access logging, 4xx body logging caps.
- Database: host, port, name, user, password; `db_uri` uses `postgresql+psycopg`.
- Redis: host, port, db, username/password, TLS flag; `redis_url` URL-encodes credentials and uses `rediss://` with certificate requirements when TLS is enabled.
- Auth: `SECRET_KEY`, algorithm, token lifetimes, minimum password length, admin seed credentials.
- Sync/scoring: sync intervals, pull sync lookback duration parser, historical sync on connect, workout sample ingestion, FIT storage, default data granularity, score backfill and scheduled score intervals.
- Provider OAuth and webhooks: provider client ids/secrets/scopes, API base URL, webhook secrets, Google service-account/project settings.
- Email: Resend API key/from address/from name/frontend URL/invitation expiry/retry count.
- AWS/raw payloads: bucket, access keys, region, SNS topic, XML chunk size, raw payload storage mode, max payload bytes, raw payload S3 bucket/prefix/endpoint.
- Svix: outgoing webhook switch, server URL, JWT secret, auth token.
- Sentry: enabled, DSN, sample rate, env, server name, git SHA.

Do not add settings that silently default to insecure production behavior. If a setting is exposed to the frontend config route, keep that response additive-only.

## Native backend test evidence map

Use these as high-signal test candidates after implementation work. They are not bundled runtime scripts and should be run from the backend checkout when dependencies/services are ready.

| Capability | Candidate tests |
| --- | --- |
| Users/auth/API keys/applications | `tests/api/v1/test_users.py`, `test_api_keys.py`, `test_applications.py`, `test_auth.py`, `test_token.py`, `test_sdk_token.py`; service/repository tests for developer, API key, application, refresh token. |
| Connections/data sources/priorities | `test_connections.py`, `test_provider_settings_service.py`, `test_priority_service.py`, data-source and priority repository tests. |
| Summaries/events/timeseries/health scores | `test_summaries.py`, `test_workouts.py`, `test_events_delete.py`, `test_health_scores.py`, `tests/services/test_summaries_service.py`, `test_time_series_service.py`, `test_event_record_service.py`, `test_health_score_service.py`. |
| Sync status/Celery tasks | `test_sync_data.py`, `test_sync_status.py`, `tests/services/test_sync_status_service.py`, `tests/tasks/test_sync_vendor_data_task.py`, `test_periodic_sync_task.py`, `test_webhook_push_task.py`. |
| Seed/data lifecycle/raw payloads | `test_seed_data.py`, `test_seed_data_service.py`, `test_raw_payload_storage.py`, archival route/service/task tests where present. |
| Outgoing webhooks | `test_outgoing_webhooks.py`, `tests/tasks/test_webhook_push_task.py`. |
| Config/security/utilities | `tests/utils_tests/test_config_utils.py`, `test_redis_url.py`, `test_auth_utils.py`, `test_security.py`, `test_access_log.py`, `test_healthcheck.py`. |
