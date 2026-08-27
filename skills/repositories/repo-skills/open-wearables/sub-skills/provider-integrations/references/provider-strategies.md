# Provider Strategy Reference

Source anchors folded into this reference: `backend/app/services/providers/`,
`backend/app/api/routes/v1/meta.py`, `backend/tests/providers/`,
`backend/tests/integrations/`, `backend/scripts/generate_coverage_docs.py`, and
`backend/app/schemas/enums/provider.py`.

## Shared types and routing behavior

- `ProviderFactory.get_provider(provider_name: str)` returns a concrete
  `BaseProviderStrategy` for the 12 verified providers.
- `ProviderName` contains the supported provider slugs plus sentinels
  `UNKNOWN` and `INTERNAL`.
- `BaseProviderStrategy.coverage` must expose `ProviderCoverage` built from the
  provider's `coverage.py` constants.
- `BaseProviderStrategy.capabilities` must return an accurate
  `ProviderCapabilities` object.
- `BaseProviderStrategy.start_historical_sync()` is the default pull-based
  implementation; Garmin overrides it for webhook backfill.
- `ProviderCapabilities` validation rules are strict:
  - `webhook_stream` and `webhook_ping` are mutually exclusive.
  - `webhook_ping` requires `rest_pull=True`.
  - `webhook_inbound_secret` requires `webhook_registration_api=True`.

Legend for coverage counts below: `ts` = timeseries, `wo` = workout_fields,
`sl` = sleep_fields, `mc` = menstrual_cycle_fields, `hs` = health_scores.

## Verified provider inventory

| Provider | Strategy | Components wired in strategy | Capability flags | Coverage (ts/wo/sl/mc/hs) | Notes |
|---|---|---|---|---|---|
| `apple` | `AppleStrategy` | `AppleWorkouts` | `client_sdk`, `file_import` | `71/13/9/0/0` | Apple Health SDK + XML import only; no cloud OAuth. |
| `samsung` | `SamsungStrategy` | `SamsungWorkouts` | `client_sdk` | `33/13/9/0/0` | SDK-only provider with no cloud API. |
| `garmin` | `GarminStrategy` | `GarminOAuth`, `GarminWorkouts`, `Garmin247Data`, `GarminWebhookHandler` | `webhook_stream`, `webhook_callback` | `29/9/9/15/3` | Push + callback backfill; historical sync is webhook-based and capped at 30 days. |
| `google` | `GoogleStrategy` | `GoogleOAuth`, `GoogleHealthApiWorkouts`, `GoogleHealth247Data`, `GoogleWebhookHandler`, `GoogleWebhookService` | `client_sdk`, `rest_pull`, `webhook_ping`, `webhook_registration_api` | `34/13/9/0/0` | Hybrid provider: Health Connect SDK plus cloud REST rollups. |
| `polar` | `PolarStrategy` | `PolarOAuth`, `PolarWorkouts`, `Polar247Data`, `PolarWebhookHandler`, `polar_webhook_service` | `rest_pull`, `webhook_ping`, `webhook_registration_api`, `webhook_inbound_secret` | `10/4/7/0/4` | Notify-only webhooks; subscription registration and inbound secret are both part of the provider contract. |
| `suunto` | `SuuntoStrategy` | `SuuntoOAuth`, `SuuntoWorkouts`, `Suunto247Data`, `SuuntoWebhookHandler` | `rest_pull`, `webhook_stream` | `6/14/8/0/1` | Full-payload webhook provider with continuous data API. |
| `whoop` | `WhoopStrategy` | `WhoopOAuth`, `WhoopWorkouts`, `Whoop247Data`, `WhoopWebhookHandler` | `rest_pull`, `webhook_ping` | `6/6/8/0/3` | Webhook payloads are notify-only; the actual data is fetched after the ping. |
| `strava` | `StravaStrategy` | `StravaOAuth`, `StravaWorkouts`, `StravaWebhookHandler`, `strava_webhook_service` | `rest_pull`, `webhook_ping`, `webhook_registration_api` | `4/12/0/0/0` | Activity-only provider; no 24/7 layer is exposed. |
| `oura` | `OuraStrategy` | `OuraOAuth`, `OuraWorkouts`, `Oura247Data`, `OuraWebhookHandler`, `oura_webhook_service` | `rest_pull`, `webhook_ping`, `webhook_registration_api` | `16/3/9/0/3` | Notify-only webhooks with programmatic subscription registration. |
| `fitbit` | `FitbitStrategy` | `FitbitOAuth`, `FitbitWorkouts` | `rest_pull` | `0/6/0/0/0` | Pull-only strategy; webhook integration is not enabled. |
| `ultrahuman` | `UltrahumanStrategy` | `UltrahumanOAuth`, `Ultrahuman247Data` | `rest_pull` | `6/0/9/0/0` | REST-only partner API; no public webhook offering in the current strategy. |
| `sensorbio` | `SensorBioStrategy` | `SensorBioOAuth`, `SensorBioWorkouts`, `SensorBio247Data` | `rest_pull` | `8/6/8/0/3` | REST-only provider with workouts and 24/7 data. |

## Component patterns

### SDK / file import providers

- **Apple** and **Samsung** wire only workouts components.
- `oauth` stays `None`.
- `api_base_url` is empty because there is no cloud API.
- Historical sync is unsupported because these providers are not REST-backed.

### Hybrid SDK + cloud provider

- **Google** combines `client_sdk=True` with `rest_pull=True`.
- The strategy wires both cloud API handlers and webhook registration support.
- Keep the provider identity singular; do not split SDK and cloud data into two provider names.

### REST + webhook stream/callback providers

- **Garmin** uses `webhook_stream=True` plus `webhook_callback=True`.
- Historical sync is a special-case webhook backfill flow, not the default pull task.
- `max_historical_days=30` is part of the capability contract.
- **Suunto** uses `webhook_stream=True` with a pull-backed API for historical and current data.

### REST + webhook ping providers

- **Oura**, **Polar**, **Strava**, and **Whoop** use `webhook_ping=True`.
- Their webhook payloads are triggers, not the full data payload.
- The handler must fetch or queue the follow-up pull work before returning success.
- **Polar** also uses `webhook_inbound_secret=True`.
- **Oura**, **Polar**, and **Strava** expose `webhook_registration_api=True`.

### REST-only providers

- **Fitbit**, **Ultrahuman**, and **SensorBio** are pull-backed only.
- They still expose `coverage` because the `/api/v1/meta/coverage` route and docs matrix rely on it.

## What to keep in sync when a strategy changes

- `coverage.py` constants
- `strategy.py` component wiring
- `ProviderFactory`
- `ProviderName`
- provider tests and integration tests
- coverage summary regeneration
- any provider-specific capability notes in the references

## Useful mental model

- `coverage.py` says *what the provider emits*.
- `strategy.py` says *how the provider delivers it*.
- `factory.py` says *how the rest of the backend finds the strategy*.
- `meta.py::_build_coverage()` says *how the public coverage matrix is assembled*.
