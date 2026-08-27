# `prefect-client` Package

## Purpose

`prefect-client` is a smaller installation that publishes a subset of the `prefect` package for lightweight environments that need to talk to Prefect Cloud or a remote Prefect server. It is useful in serverless functions, short-lived jobs, and resource-constrained containers.

It shares Python support with Prefect: Python `>=3.10,<3.15`.

## What It Keeps

The package is designed for remote API interaction. Typical supported patterns include:

- `from prefect.client.orchestration import get_client`
- Direct orchestration client calls against a configured `PREFECT_API_URL`.
- `prefect.client.schemas.*` models for filters, sorting, actions, objects, and responses.
- Selected high-level client-facing helpers, such as deployment run helpers and event emission where the package includes the required modules.
- Settings needed to configure API URL, API key, custom headers, TLS, retry behavior, and profiles.

Example remote query:

```python
from prefect.client.orchestration import get_client

async def query_api():
    async with get_client() as client:
        return await client.read_concurrency_limits(limit=10, offset=0)
```

## What It Omits

By design, `prefect-client` omits all CLI and server components. Consequences:

- The `prefect` console script is not available from `prefect-client` alone.
- Server objects and modules may fail to import or fail at runtime.
- Some imports may exist but are not runnable if they rely on server-oriented functionality.
- Local CLI workflows, server startup, and repo-maintenance tasks require the full `prefect` package.

If code imports server internals, CLI modules, or starts local services, route it to the full `prefect` package and the sibling sub-skills for CLI/server or repo development.

## Configuration Requirements

`prefect-client` expects a remote API connection:

```bash
export PREFECT_API_URL="https://api.prefect.cloud/api/accounts/<account-id>/workspaces/<workspace-id>"
export PREFECT_API_KEY="<api-key>"
```

For self-hosted Prefect, use the self-hosted API URL instead. Avoid relying on ephemeral server mode in lightweight `prefect-client` deployments because the server components are intentionally absent.

## Package Split Evidence

The client package uses `client/pyproject.toml` and builds the same top-level `prefect` package name from a curated source subset. Its dependencies focus on HTTP, Pydantic models, settings, serialization, events, and lightweight runtime support. The full `prefect` distribution includes additional server, CLI, database, and orchestration service functionality.

When maintaining package metadata, keep the split in mind:

- Runtime usage guidance should avoid server/CLI imports for `prefect-client` users.
- Repo-development changes that alter shared dependencies or source selection need maintainer checks in `../repo-development/SKILL.md`.
- User-facing code examples should state whether they require full `prefect` or work with `prefect-client`.

## Custom SDK Route

The generated deployment SDK is different from `prefect-client`: it is a typed Python file generated from live deployment metadata. It still needs an active Prefect API connection and a compatible Prefect client runtime. Use it when agents need autocomplete and typed `.run()` / `.run_async()` helpers for known deployments.

Regenerate when server-side deployment metadata changes:

- Deployment added, removed, or renamed.
- Flow parameter schema changes.
- Work pool job variable schema changes.

## Validation Checklist

- If the environment only has `prefect-client`, avoid `prefect` CLI commands and server imports.
- Confirm `PREFECT_API_URL` points to a reachable remote API; do not expect local server startup support.
- Confirm `PREFECT_API_KEY` for Prefect Cloud.
- Prefer direct `get_client` imports from `prefect.client.orchestration` for clarity in lightweight code.
- If an import exists but runtime behavior reaches server internals, switch to full `prefect` or redesign around remote client calls.
