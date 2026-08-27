# API Client Reference

## Client Selection

Prefect exposes orchestration clients through `prefect.get_client` and `prefect.client.orchestration.get_client`.

- Default: `get_client()` returns an asynchronous `PrefectClient` and must be used as an async context manager.
- Synchronous: `get_client(sync_client=True)` returns a `SyncPrefectClient` and must be used as a normal context manager.
- Advanced HTTP settings: pass `httpx_settings={...}` to tune the underlying HTTPX client, for example timeouts or proxy behavior.
- Context reuse: inside an existing Prefect client context, `get_client` can return the context client when the HTTPX settings and event loop match.

```python
from prefect import get_client

async with get_client() as client:
    response = await client.hello()
    print(response.json())
```

```python
from prefect import get_client

with get_client(sync_client=True) as client:
    response = client.hello()
    print(response.json())
```

Do not mix these boundaries: async client methods are awaited, sync client methods are not. A common bug is calling `await` on a sync client method or forgetting `await` on an async client method.

## API URL and Ephemeral Mode

`get_client` reads `PREFECT_API_URL` from the settings system.

- If `PREFECT_API_URL` is set, clients point at that REST API URL.
- If `PREFECT_API_URL` is unset and `PREFECT_SERVER_ALLOW_EPHEMERAL_MODE` is enabled, Prefect may create an ephemeral API process and use its API URL.
- If `PREFECT_API_URL` is unset and ephemeral mode is disabled, `get_client` raises `ValueError` asking for a running Prefect server API URL.
- For Prefect Cloud, use the Cloud API URL form `https://api.prefect.cloud/api/accounts/<account-id>/workspaces/<workspace-id>` plus an API key.

For code that should work in both local ephemeral mode and configured remote mode, avoid hard-coding a URL. Accept an optional URL argument and use `temporary_settings` only around the client block when an override is needed.

```python
from prefect import get_client
from prefect.settings import PREFECT_API_URL, temporary_settings

async def list_deployments(api_url: str | None = None):
    updates = {PREFECT_API_URL: api_url} if api_url else {}
    with temporary_settings(updates=updates):
        async with get_client() as client:
            return await client.read_deployments(limit=20, offset=0)
```

## Authentication and Headers

Common client settings:

- `PREFECT_API_KEY`: API key for Prefect Cloud or authenticated API deployments.
- `PREFECT_API_AUTH_STRING`: alternate auth string passed into clients.
- `PREFECT_CLIENT_CUSTOM_HEADERS`: JSON object of extra HTTP headers for proxies or gateways.

Prefect protects selected headers from being overridden by custom headers, including `User-Agent`, `Prefect-Csrf-Token`, and `Prefect-Csrf-Client`. Client tests verify that custom headers are accepted, but protected CSRF/User-Agent headers are ignored or preserved.

## Schema Models

Use Pydantic models under `prefect.client.schemas` when a client method expects filters, sorting, actions, objects, or responses.

Common imports:

```python
from prefect.client.schemas.filters import FlowRunFilter, DeploymentFilter
from prefect.client.schemas.sorting import FlowRunSort
from prefect.client.schemas.objects import FlowRun
from prefect.client.schemas.actions import WorkPoolCreate
```

Patterns:

- Construct filters with nested dictionaries matching the model fields, for example `FlowRunFilter(state={"name": {"any_": ["Late"]}})`.
- Use sort enums from `prefect.client.schemas.sorting` rather than raw strings when available.
- Let Pydantic raise validation errors locally before making network requests.
- Paginate calls that accept `limit` and `offset`; server-side defaults may cap results, commonly around `PREFECT_API_DEFAULT_LIMIT`.

## Direct Client vs Higher-Level SDK

Use direct clients when the operation is not cleanly covered by decorators or high-level helpers, such as bulk rescheduling, custom filters, read-only diagnostics, or administrative queries. Route flow/task authoring to `../flow-task-authoring/SKILL.md` and deployment/work-pool command construction to `../deployments-workers/SKILL.md`.

## Generated Deployment SDK

The custom SDK route generates a typed Python file from deployments using `prefect sdk generate`. It requires an active API connection and existing deployments. The generated module exposes typed deployment helpers such as `deployments.from_name(...).run(...)`, `run_async(...)`, `with_options(...)`, and `with_infra(...)`. Regenerate after deployment names, parameter schemas, or work-pool job variable schemas change. CLI usage details belong in `../cli-server-operations/SKILL.md`; this sub-skill covers the API shape and sync/async usage once the generated SDK exists.

## Validation Checklist

- Import `get_client` from `prefect` or `prefect.client.orchestration`.
- Use `async with` plus `await` for `PrefectClient`; use `with` and no `await` for `SyncPrefectClient`.
- Confirm `PREFECT_API_URL` or ephemeral mode before opening the client.
- For Cloud, confirm `PREFECT_API_KEY` and the `/api/accounts/.../workspaces/...` URL shape.
- Build filters and actions with `prefect.client.schemas.*` models and catch Pydantic validation errors early.
