# Coverage and Sync

This reference explains the provider coverage contract, how sync/backfill works,
and how the backend coverage matrix is assembled.

## Source of truth

- `coverage.py` inside each provider package defines what the provider emits.
- `ProviderCoverage` carries the declared data dimensions:
  - `timeseries`
  - `workout_fields`
  - `sleep_fields`
  - `menstrual_cycle_fields`
  - `health_scores`
- `ProviderCapabilities` describes how the provider delivers data.
- `backend/app/api/routes/v1/meta.py::_build_coverage()` reads every provider
  through `ProviderFactory` and assembles the public coverage matrix.
- The skill-local helper `scripts/generate_coverage_docs.py` renders a compact
  summary from the same verified provider inventory.

## Coverage guard behavior

The repo-native guard test `backend/tests/providers/test_provider_coverage.py`
checks three things:

1. emitted `SeriesType` values must be declared in the provider's `TIMESERIES`
2. emitted detail fields must appear in `WORKOUT_FIELDS`, `SLEEP_FIELDS`, or
   `MENSTRUAL_CYCLE_FIELDS`
3. the strategy's `coverage` property must expose the exact same values as the
   provider's `coverage.py`

That means a provider update must touch both implementation and coverage data.
If a handler emits a new field or metric, the coverage constants must move with
it or the guard will fail.

## Sync and backfill model

### Default historical sync

`BaseProviderStrategy.start_historical_sync()` is the default pull-based path.
If `capabilities.rest_pull` is `True`, it queues the vendor sync task with
`is_historical=True` and returns a `HistoricalSyncResult` with:

- `method="pull_api"`
- `days=<requested days>`
- `start_date` and `end_date` populated

### Garmin override

Garmin does not use the default pull-based historical sync.
Its strategy overrides `start_historical_sync()` to launch the Garmin backfill
task and return a `HistoricalSyncResult` with:

- `method="webhook_backfill"`
- `days=None`
- no start/end window in the result

### Default live sync mode

`BaseProviderStrategy.default_live_sync_mode` derives the setting from
`ProviderCapabilities`:

- `rest_pull=True` → `LiveSyncMode.PULL`
- `client_sdk=True` and no REST/webhook support → `None`
- webhook-only providers → `LiveSyncMode.WEBHOOK`

### Webhook delivery rules

- `webhook_stream` means the webhook body contains the full payload.
- `webhook_ping` means the webhook is only a trigger; the handler must fetch the
  actual data after the ping.
- `webhook_registration_api=True` means the provider can register its webhook
  subscriptions programmatically.
- `webhook_inbound_secret=True` means the inbound signature secret is returned
  by the provider registration flow and persisted in provider settings.

### Special-case providers

- **Apple** and **Samsung** are SDK/file-import providers; they do not support
  server-side historical sync.
- **Google** is a hybrid provider: SDK + REST + webhook ping.
- **Garmin** uses webhook stream + callback backfill and has a 30-day historical
  cap.
- **Polar** uses webhook ping plus an inbound secret.
- **Strava** and **Oura** use webhook ping plus programmatic webhook
  registration.
- **Ultrahuman**, **Fitbit**, and **SensorBio** are REST-backed without webhook
  delivery in the current strategy.

## Provider count invariant

The verified inventory contains 12 providers:

- Apple
- Samsung
- Garmin
- Google
- Polar
- Suunto
- Whoop
- Strava
- Oura
- Fitbit
- Ultrahuman
- SensorBio

The helper script `scripts/provider_inventory.py --check-count` should continue
reporting 12 unless the inventory itself is intentionally expanded.

## Update order when coverage changes

1. Update the provider's implementation.
2. Update `coverage.py`.
3. Update `strategy.py` to pass through the new coverage constants.
4. Refresh provider-specific tests.
5. Validate the public metadata contract by checking that `/api/v1/meta/coverage` still has the same response shape and now includes the changed provider coverage. Use `backend-core` for route/OpenAPI contract checks only when the metadata endpoint shape, auth, tags, or docs navigation changes.
6. Regenerate or check the coverage summary/docs. The bundled helper renders a skill-local summary; repo docs regeneration remains a maintainer action after provider changes.
7. Re-check the provider count and capability consistency.
8. In the portal, no React change is normally required when the `/api/v1/meta/coverage` shape is unchanged because the coverage page consumes `useCoverage`/`meta.coverage()` data. Route to `frontend-portal` only if the response shape, display labels/grouping, provider icon data, or UI behavior changes.

## Common sync/backfill mistakes

- calling the default historical sync on an SDK-only provider
- adding `webhook_ping=True` without `rest_pull=True`
- using both `webhook_ping` and `webhook_stream`
- adding a webhook inbound secret without a registration API
- changing the handler's emitted fields without updating `coverage.py`
