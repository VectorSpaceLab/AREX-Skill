---
name: api-client-settings
description: "Use Prefect Python clients, settings, profiles, schemas, and the
  prefect-client package split safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Prefect API Client and Settings

Use this sub-skill when a task needs direct Python access to Prefect orchestration or Cloud APIs, settings/profile diagnosis, schema-model construction, or the lightweight `prefect-client` package boundary.

## Start Here

1. Choose the client style in [references/api-reference.md](references/api-reference.md): `async with get_client()` for async code, `with get_client(sync_client=True)` for synchronous code.
2. Confirm configuration in [references/settings-and-profiles.md](references/settings-and-profiles.md): `PREFECT_API_URL`, `PREFECT_API_KEY`, active profile, and source precedence.
3. If the environment uses `prefect-client` instead of the full `prefect` package, read [references/prefect-client-package.md](references/prefect-client-package.md) before importing CLI/server modules.
4. For failures, use [references/troubleshooting.md](references/troubleshooting.md) and the bundled `scripts/inspect_prefect_settings.py` helper.

## Use For

- `get_client`, `PrefectClient`, `SyncPrefectClient`, and direct REST API method calls.
- Pydantic schema objects under `prefect.client.schemas.*` for filters, sorts, actions, objects, and responses.
- `get_current_settings`, `temporary_settings`, settings accessors, environment variables, `.env`, `prefect.toml`, `pyproject.toml`, and profiles TOML.
- `prefect-client` package behavior and custom generated deployment SDK usage patterns.

## Route Elsewhere

- Server implementation internals, generated schema maintenance, and repo test selection: `../repo-development/SKILL.md`.
- CLI command operations, server startup, Cloud login commands, and profile/config command usage: `../cli-server-operations/SKILL.md`.
- Flow/task decorators, execution semantics, states, futures, and task runners: `../flow-task-authoring/SKILL.md`.
- Deployment creation, work pools, workers, and deployment YAML: `../deployments-workers/SKILL.md`.

## Safe Validation

- Inspect effective settings without network calls:

```bash
python scripts/inspect_prefect_settings.py --schema-summary
```

- Validate a profiles TOML file before relying on it:

```bash
python scripts/inspect_prefect_settings.py --validate-profiles --profiles-path ~/.prefect/profiles.toml
```

- For client code, prefer tiny `hello()` or read-only list/filter calls against a known API URL; do not start long-lived services from this sub-skill.
