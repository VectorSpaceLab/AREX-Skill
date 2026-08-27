---
name: server-and-stores
description: "Work on ZenML FastAPI server routers, auth/RBAC, domain models,
  stores, SQLModel schemas, Alembic migrations, triggers, resource pools, and
  server deployment troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Server and Stores

Use this sub-skill when the task mentions ZenML FastAPI, REST endpoints, routers, `zen_server`, authentication, RBAC, HTTP errors, Zen stores, SQLModel schemas, Alembic migrations, triggers, schedules, resource pools, resource requests, server deployment, database upgrades, or server optional extras.

## When To Read

- Read [Server API](references/server-api.md) before adding or debugging FastAPI routers, endpoint wrappers, auth/RBAC checks, HTTP exceptions, feature gates, server optional dependencies, or import-boundary failures.
- Read [Models, Stores, and Migrations](references/models-stores-migrations.md) before changing Pydantic domain models, filters, REST/SQL store methods, SQLModel schemas, migrations, triggers, resource pools, or rolling-compatible data shapes.
- Read [Troubleshooting](references/troubleshooting.md) when server extras are missing, FastAPI returns the wrong status, RBAC blocks a request, schema/model fields drift, migrations diverge, trigger/resource-pool updates miss a layer, or upgrades break rolling deployments.
- Run [check_migration_branches.py](scripts/check_migration_branches.py) after adding or rebasing Alembic revisions to detect diverging migration heads without mutating any database.

## Scope

This sub-skill owns ZenML server internals: FastAPI app and routers, `zen_server`-local utilities, auth/RBAC endpoint patterns, REST server behavior, Zen store interfaces and implementations, SQLModel schemas, Alembic migrations, trigger/resource-pool internals, and server deployment troubleshooting. Keep runtime behavior synchronous at route boundaries unless the existing async wrapper pattern requires otherwise.

## Route Elsewhere

- Use [CLI and Client](../cli-and-client/SKILL.md) for Click commands, `Client()` usage, login/connect flows, user-facing list filters, and CLI/client signature coupling.
- Use [Pipeline Authoring](../pipeline-authoring/SKILL.md) for `@pipeline`, `@step`, schedules as authoring APIs, materializers, hooks, cache/retry behavior, and local pipeline runs.
- Use [Stacks and Integrations](../stacks-and-integrations/SKILL.md) for stack component flavors, service connectors, orchestrators, step operators, integration extras, and optional SDK import boundaries.
- Use [Maintenance](../maintenance/SKILL.md) for targeted test selection, formatting, linting, spelling, CI-equivalent checks, and broad docs maintenance.

## Safe Defaults

Do not import `zenml.zen_server` from client, CLI, integration, or shared model code. Do not import SQL schemas or `SqlZenStore` from outside the store/server layer; use shared models or `Client().zen_store` when lower-level access is unavoidable. Prefer read-only probes, `--help`, targeted unit tests, and branch checks before any migration upgrade. Treat tokens, API keys, database URLs, secret values, server URLs, and backup credentials as sensitive.
