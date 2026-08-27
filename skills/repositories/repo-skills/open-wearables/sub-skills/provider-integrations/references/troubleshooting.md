# Provider Integrations Troubleshooting

## Fast triage order

1. Check the provider slug in `ProviderName` and `ProviderFactory`.
2. Check the strategy's `capabilities` and `coverage` properties.
3. Check the provider-specific tests.
4. Check `coverage.py` for stale constants.
5. Regenerate the skill-local coverage summary if the inventory changed.

## Common failures

| Symptom | Likely cause | First check | Likely fix |
|---|---|---|---|
| `Unknown provider: ...` | Factory and enum are out of sync | `backend/app/services/providers/factory.py` and `backend/app/schemas/enums/provider.py` | Add the provider slug to both places. |
| `ProviderCapabilities` raises `ValueError` | Invalid capability combination | The capability flags in `strategy.py` | Remove conflicting flags; `webhook_ping` cannot coexist with `webhook_stream`, and `webhook_ping` requires `rest_pull=True`. |
| Historical sync is rejected | Provider is SDK-only or push-only | `capabilities.rest_pull` and any strategy override | Use the provider's push/import path or implement a custom historical sync. |
| Webhook returns `401` | Signature or challenge handling mismatch | The provider handler's `verify_signature()` / `handle_challenge()` | Check the provider-specific header, token, or HMAC secret. |
| Webhook returns `501` for GET | Challenge route not implemented | `BaseWebhookHandler.handle_challenge()` override | Implement the provider-specific challenge response. |
| Webhook ping arrives but no data is saved | Notify-only webhook path does not fetch or queue the follow-up pull | `dispatch()` in the webhook handler | Queue the REST fetch or Celery task before returning success. |
| Coverage guard fails | New series or detail field was added without coverage updates | `coverage.py` and the emitting handler | Add the new field/metric to the matching coverage constant. |
| Coverage summary looks stale | Inventory changed but the summary was not regenerated | `scripts/generate_coverage_docs.py` | Regenerate the summary and sync the references. |
| OAuth callback says provider mismatch | The stored state was created for a different provider or expired | OAuth state creation and callback flow | Recreate the auth URL and confirm the provider slug. |
| Webhook registration never happens | Missing registration API flag or missing service wiring | `webhook_registration_api` and `webhook_service` | Implement the registration service or keep the provider manual-setup only. |

## Provider-specific clues

- **Apple / Samsung**: no cloud API; `oauth` should remain `None`.
- **Garmin**: historical sync is a backfill task, not the default pull API.
- **Google**: one provider identity covers both SDK and cloud data.
- **Polar**: inbound secret verification depends on the registration flow.
- **Strava / Oura**: the webhook payload is a trigger, not the full dataset.
- **Ultrahuman / Fitbit / SensorBio**: REST-backed providers with no webhook
  delivery in the current strategy.

## Safe checks

- `python scripts/provider_inventory.py --check-count`
- `python scripts/generate_coverage_docs.py --check <file>`
- repo-native guard test: `backend/tests/providers/test_provider_coverage.py`
- repo-native factory test: `backend/tests/providers/test_provider_factory.py`

## What not to do

- Do not call live provider APIs during a basic skill check.
- Do not use credentials to prove the inventory.
- Do not treat the UI coverage matrix as the source of truth for backend coverage.
