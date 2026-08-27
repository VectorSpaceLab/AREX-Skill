# REST service configuration

## Settings model

`graph_service.config.Settings` is a `BaseSettings` model with these fields:

- `openai_api_key`
- `openai_base_url`
- `model_name`
- `embedding_model_name`
- `neo4j_uri`
- `neo4j_user`
- `neo4j_password`
- `falkordb_host`
- `falkordb_port`
- `falkordb_database`
- `db_backend` (default `neo4j`)

The app loads settings from `.env` and the environment. Missing `openai_api_key`
usually fails startup because the default Graphiti clients need it.

## Runtime environment variables

| Variable | Use |
| --- | --- |
| `OPENAI_API_KEY` | Required for the default LLM/embedder path. |
| `OPENAI_BASE_URL` | Optional OpenAI-compatible or Azure endpoint override. |
| `MODEL_NAME` | LLM model name. |
| `EMBEDDING_MODEL_NAME` | Embedder model name. |
| `NEO4J_URI` | Neo4j bolt URI. |
| `NEO4J_USER` | Neo4j username. |
| `NEO4J_PASSWORD` | Neo4j password. |
| `FALKORDB_HOST` | FalkorDB host when using the Falkor path. |
| `FALKORDB_PORT` | FalkorDB port. |
| `FALKORDB_DATABASE` | FalkorDB graph/database name. |
| `DB_BACKEND` | Selects `neo4j` or `falkordb`. |

## Service startup

The repository provides two common startup patterns:

### Uvicorn

```bash
OPENAI_API_KEY=... DB_BACKEND=neo4j uv run uvicorn graph_service.main:app --host 0.0.0.0 --port 8000
```

### Docker Compose

The repo's Compose files start the graph backend and the REST service together.
Use the Neo4j or FalkorDB profile that matches the workflow.

## Package and verification commands

Useful commands from the repo's service layout:

- `make install` in `server/` installs the service dev dependencies.
- `make test` in `server/` runs the service tests.
- `pytest server/tests/test_live_falkordb_int.py -q` exercises the live FalkorDB path.

## Backend behavior

- The default service backend is Neo4j.
- The service can be pointed at FalkorDB for the live integration path.
- `graph_service.zep_graphiti.ZepGraphiti` wraps the core SDK and exposes service
  convenience methods like `save_entity_node`, `delete_group`, and `search`.

## Polling and timing

Because `/messages` is queued, scripts and operators should:

1. call `/healthcheck`,
2. send `/messages`,
3. poll `/episodes/{group_id}`,
4. then search.

That pattern avoids false negatives when the queue has not finished processing.
