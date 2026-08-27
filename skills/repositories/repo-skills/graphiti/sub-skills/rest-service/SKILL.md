---
name: rest-service
description: "Guides Graphiti FastAPI REST service routes, configuration,
  deployment, and smoke checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# rest-service

Use this sub-skill for the Graphiti FastAPI service surface. It covers route
behavior, request/response shapes, queue semantics, environment variables, Docker
startup, health checks, and live REST smoke testing.

## Read first

- `references/rest-api.md` for endpoint paths, request models, response shapes,
  and queue semantics.
- `references/configuration.md` for service settings, backend variables, Docker
  and Uvicorn startup patterns, and test commands.
- `references/troubleshooting.md` when startup fails, `/messages` returns before
  search is ready, or a backend/credential mismatch blocks the service.
- `scripts/graph_service_smoke.py` to exercise `/healthcheck`, `/messages`,
  `/episodes`, and `/search` against a running service.

## What belongs here

Use this sub-skill when the task mentions:

- `graph_service.main:app`, `ZepGraphiti`, or the service `Settings` model
- `/healthcheck`, `/messages`, `/entity-node`, `/search`, `/entity-edge`,
  `/episodes`, `/get-memory`, `/group`, or `/clear`
- `DB_BACKEND`, `NEO4J_*`, or `FALKORDB_*` variables for the REST API
- REST service Docker or Uvicorn deployment
- the service's async message ingestion queue

## What does not belong here

Route these elsewhere:

- Direct Python SDK use -> `sub-skills/core-sdk/`
- MCP tool names, transports, config YAML, or MCP Docker variants -> `sub-skills/mcp-server/`
- General FastAPI theory that is not tied to Graphiti's routes or settings

## REST workflow

1. Start a graph backend.
2. Set `OPENAI_API_KEY` and backend-specific variables.
3. Start the FastAPI app.
4. Call `/healthcheck`.
5. POST messages or entity nodes.
6. Poll `/episodes/{group_id}` before assuming queued ingestion has completed.
7. Query `/search` or `/get-memory`.
8. Delete test groups or call `/clear` only when intentional.

## Important route semantics

- `POST /messages` returns `202 Accepted` and queues work. It does not prove the
  episode has already been processed.
- `POST /entity-node` creates a node directly and returns it.
- `POST /search` searches fact edges and returns a `facts` list.
- `GET /episodes/{group_id}` is the most useful polling path after `/messages`.
- `POST /clear` and `DELETE /group/{group_id}` are destructive.

## Validation path

For a running service:

```bash
python scripts/graph_service_smoke.py --base-url http://127.0.0.1:8000
```

Use `--health-only` when you only need startup validation, and use the full smoke
when you have a live backend plus model credentials.
