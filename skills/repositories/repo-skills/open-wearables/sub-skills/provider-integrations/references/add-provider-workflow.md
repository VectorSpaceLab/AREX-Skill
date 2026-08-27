# Add or Update a Provider Workflow

This workflow is for provider strategy changes, capability changes, OAuth or
webhook wiring, sync/backfill behavior, and provider-specific test coverage.
If the task is only about generic backend routes or auth plumbing, hand it to
`../backend-core/` instead.

## 1. Choose the delivery model first

Match the new provider to one of the established patterns:

- **SDK / file import**: Apple, Samsung
- **Hybrid SDK + cloud**: Google
- **REST pull + webhook stream**: Garmin, Suunto
- **REST pull + webhook ping**: Oura, Polar, Strava, Whoop
- **REST only**: Fitbit, Ultrahuman, SensorBio

Then decide which `ProviderCapabilities` flags are needed:

- `rest_pull`
- `client_sdk`
- `file_import`
- `webhook_callback`
- `webhook_stream`
- `webhook_ping`
- `webhook_registration_api`
- `webhook_inbound_secret`
- `max_historical_days`

Remember the validation rules:

- `webhook_stream` and `webhook_ping` cannot both be `True`.
- `webhook_ping` requires `rest_pull=True`.
- `webhook_inbound_secret` requires `webhook_registration_api=True`.

## 2. Create the provider package

Create `backend/app/services/providers/<provider>/` with the smallest set of
modules the provider actually needs:

- `strategy.py`
- `coverage.py`
- `oauth.py` when the provider uses cloud OAuth
- `workouts.py` when workout/activity data is supported
- `data_247.py` when sleep/recovery/continuous data is supported
- `webhook_handler.py` when the provider receives webhooks
- `webhook_service.py` when the provider supports programmatic webhook
  subscription management

## 3. Define `coverage.py` before wiring the strategy

`coverage.py` is the single source of truth for emitted data.
Use these exact names:

- `TIMESERIES`
- `WORKOUT_FIELDS`
- `SLEEP_FIELDS`
- `MENSTRUAL_CYCLE_FIELDS`
- `HEALTH_SCORES`

Guidelines:

- Build the constants from the actual handler mappings when possible.
- Use `frozenset()` for layers the provider does not emit.
- Keep the provider's strategy coverage property a direct pass-through.
- If the implementation emits a new `SeriesType` or writes a new detail field,
  update the matching constant before merging.

## 4. Implement `strategy.py`

Subclass `BaseProviderStrategy` and set the provider identity, API base URL, and
component wiring.

Minimum properties:

- `name`
- `api_base_url`
- optional `display_name`
- `capabilities`
- `coverage`

Common component wiring patterns:

- `self.oauth = ...` for OAuth-backed providers
- `self.workouts = ...` for workout/activity providers
- `self.data_247 = ...` for sleep/recovery/activity sample providers
- `self.webhooks = ...` for webhook delivery
- `self.webhook_service = ...` for webhook subscription management

Override `start_historical_sync()` only when the default pull-based implementation
is wrong. Garmin is the known special case.

## 5. Wire OAuth correctly when needed

If the provider uses OAuth, follow the existing template contract:

- build `ProviderEndpoints`
- build `ProviderCredentials`
- set `use_pkce` only when the provider requires PKCE
- choose `AuthenticationMethod.BASIC_AUTH` or `AuthenticationMethod.BODY`
- implement `_get_provider_user_info()`

A provider that is SDK/file-import-only should leave `oauth = None`.

## 6. Register the provider

Update both of these source locations:

- `backend/app/services/providers/factory.py`
- `backend/app/schemas/enums/provider.py`

The factory must return the new strategy, and the enum must expose the new slug.
If either side is missing, provider lookup and coverage assembly will drift.

## 7. Add or refresh tests

At minimum, add coverage for:

- factory lookup for the new provider
- strategy construction and component types
- capability flags
- coverage property exposure
- provider-specific OAuth, import, webhook, or backfill behavior

Useful existing guard files in the repo:

- `backend/tests/providers/test_provider_factory.py`
- `backend/tests/providers/test_provider_coverage.py`
- `backend/tests/providers/test_historical_sync.py`
- `backend/tests/integrations/test_provider_oauth.py`
- provider-specific tests under `backend/tests/providers/<provider>/`
- provider integration tests under `backend/tests/integrations/`

## 8. Refresh coverage docs and inventory

After coverage changes, keep the skill-local summary in sync with the current
inventory using `scripts/generate_coverage_docs.py`.

If you are also changing the source repository's coverage page, remember that
`backend/app/api/routes/v1/meta.py::_build_coverage()` is the backend source of
truth for the public coverage matrix.

## 9. Sanity-check before handoff

- the provider count still matches the verified 12-provider inventory
- `ProviderCapabilities` values are internally consistent
- strategy wiring matches the actual delivery model
- tests cover the new path without live provider calls or credentials
- docs regeneration is deterministic and safe by default

## Minimal change checklist

- [ ] provider folder created
- [ ] `coverage.py` constants added or updated
- [ ] `strategy.py` wired
- [ ] `oauth.py` / `workouts.py` / `data_247.py` / `webhook_handler.py` added if needed
- [ ] factory updated
- [ ] provider enum updated
- [ ] tests added or refreshed
- [ ] coverage summary regenerated
- [ ] provider inventory still reports 12 providers
