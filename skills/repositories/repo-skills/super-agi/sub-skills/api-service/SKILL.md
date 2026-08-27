---
name: api-service
description: "Guides SuperAGI FastAPI routes, API-key and JWT auth, webhooks,
  migrations, and SQLAlchemy-backed service debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SuperAGI API Service

Use this sub-skill when the task is about SuperAGI's FastAPI service, public API
routes, auth, webhooks, or database-backed service behavior.

## Read First

- [references/api-reference.md](references/api-reference.md) for route families,
  prefixes, and important request/response types.
- [references/data-models.md](references/data-models.md) for the SQLAlchemy
  entities and relationship hints used by the service.
- [references/auth-and-webhooks.md](references/auth-and-webhooks.md) for JWT,
  API-key, GitHub OAuth, and webhook behavior.
- [references/troubleshooting.md](references/troubleshooting.md) for route,
  import, DB, auth, and migration failures.
- [scripts/inspect_superagi_routes.py](scripts/inspect_superagi_routes.py) for a
  safe static route inventory from a checkout.

## Core Route Groups

SuperAGI's `main.py` registers many routers under stable prefixes:

- `/users`, `/organisations`, `/projects`
- `/budgets`, `/agents`, `/agentexecutions`, `/agentexecutionfeeds`,
  `/agentexecutionpermissions`
- `/resources`, `/configs`, `/toolkits`, `/tool_configs`
- `/agent_templates`, `/agent_workflows`, `/analytics`, `/models_controller`
- `/google`, `/twitter`, `/knowledges`, `/knowledge_configs`
- `/vector_dbs`, `/vector_db_indices`, `/marketplace`, `/api-keys`, `/v1/agent`
- `/webhook`

Use the API reference for endpoint-level selection; keep the root router map in
mind when a caller names only a resource or action.

## Typical Decisions

1. **Login/API-key path vs GUI session path:** Choose the JWT routes in `main.py`
   for browser/login flows and the API-key protected `/v1/agent` routes for
   external automation.
2. **API route vs model/tool route:** If the task is about a request/response
   shape or status code, stay in this sub-skill. If the task is about what a
   workflow does after the request, route to `agents-workflows` or
   `toolkits-integrations`.
3. **Schema vs behavior:** Use `data-models.md` for entity shapes and
   `inspect_superagi_routes.py` for route discovery before making changes or
   writing a new reference.
4. **Migration sensitivity:** The app seeds and migration state influence many
   endpoints. When the database layout is involved, check whether the user needs
   a schema fix or only a controller call.

## Safe Workflow

- Use the static route inspector before importing `main.py` if the goal is only
  to understand endpoint coverage.
- Treat the FastAPI app as side-effectful: importing `main.py` can construct a DB
  engine and register startup handlers.
- Avoid starting the live API unless the downstream user explicitly wants that
  effect and the PostgreSQL/Redis dependencies are available.

## Boundary Notes

- Deployment topology, config file values, and container startup belong to
  `deployment-configuration`.
- Tool execution, toolkit registration, and marketplace tool downloads belong to
  `toolkits-integrations`.
- Agent workflow execution, prompts, parsing, and Celery background behavior
  belong to `agents-workflows`.
- Provider, resource, and vector DB settings that are only needed to satisfy API
  requests belong to `models-resources-vector`.
