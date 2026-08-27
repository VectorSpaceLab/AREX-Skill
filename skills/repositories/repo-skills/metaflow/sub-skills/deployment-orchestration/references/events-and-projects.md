# Events, Projects, Schedules, and Secrets

## Projects

`@project(name=...)` namespaces production and branch workflows. Project-aware names affect triggers and deployment names.

## Schedules

`@schedule` supports `cron`, `weekly`, `daily`, `hourly`, and `timezone` attributes. Only one scheduling style should be active for a flow.

## Events

`@trigger(event=...)` accepts a string, dict, list of event dicts via `events`, and deploy-time callables. Dict events must include `name` and may include `parameters` mappings. `@trigger_on_finish(flow=...)` or `flows=[...]` depends on upstream flow completion and respects project-aware names.

`namespaced_event_name("event")` can construct project-aware event names at deploy time.

## Secrets

`@secrets(sources=[...], role=None, allow_override=False)` injects secrets from configured providers. Backends include inline, AWS Secrets Manager, GCP Secret Manager, and Azure Key Vault providers. Do not print secret values during diagnostics.
