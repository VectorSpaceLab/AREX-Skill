---
name: graphiti
description: "Routes Graphiti SDK, REST service, and MCP server workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Graphiti

Graphiti builds temporal context graphs for AI agents. Use this skill when the task
mentions the Graphiti Python SDK, graph ingestion/search, custom node or edge types,
Neo4j or FalkorDB backends, the REST service, or the MCP server.

## Start here

- Read `references/installation-and-backends.md` for the public install commands,
  required environment variables, backend choices, and the first import check.
- Read `references/workflows.md` when you need the shortest route to a working
  ingest/search, REST, or MCP flow.
- Read `references/troubleshooting.md` when Graphiti fails to import, a backend is
  missing, a provider is misconfigured, or a workflow returns validation errors.
- Run `scripts/check_graphiti_install.py` if you need a quick, local verification of
  the installed package surface before doing anything more specific.

## Route to the right sub-skill

### `sub-skills/core-sdk/`
Use this for the Python library itself: `Graphiti`, drivers, ingest, search,
triplets, custom types, provider configuration, and quickstart-style workflows.

Read this sub-skill when the task mentions:
- `graphiti_core`, `Graphiti`, `Neo4jDriver`, `FalkorDriver`, or `OpenAIGenericClient`
- episode ingestion, `add_episode`, `add_episode_bulk`, `search`, `search_`,
  `retrieve_episodes`, `build_communities`, `summarize_saga`, or `add_triplet`
- custom entity or edge types, `edge_type_map`, `excluded_entity_types`,
  `previous_episode_uuids`, or `custom_extraction_instructions`
- search recipes such as `NODE_HYBRID_SEARCH_RRF` or `EDGE_HYBRID_SEARCH_CROSS_ENCODER`
- tracing, telemetry, structured output, or provider selection for the SDK

### `sub-skills/rest-service/`
Use this for the FastAPI REST service in `server/`: routes, request/response
schemas, queue behavior, health checks, Docker deployment, and service-side
backend configuration.

Read this sub-skill when the task mentions:
- `/messages`, `/search`, `/entity-node`, `/entity-edge`, `/episodes`, `/get-memory`,
  `/clear`, or `/healthcheck`
- `graph_service.main`, `ZepGraphiti`, `Settings`, `DB_BACKEND`, or the service queue
- `graph-service`, `uvicorn`, Docker Compose, or live REST integration behavior

### `sub-skills/mcp-server/`
Use this for the MCP server in `mcp_server/`: tool catalog, transports, config
schema, queueing, custom entity and edge types, and Docker deployment.

Read this sub-skill when the task mentions:
- `graphiti_mcp_server`, `main.py`, `--transport`, `stdio`, `http`, or `sse`
- `add_memory`, `search_nodes`, `search_memory_facts`, `get_episodes`,
  `summarize_saga`, `build_communities`, `add_triplet`, `get_episode_entities`,
  `clear_graph`, or `get_status`
- `config.yaml`, `GraphitiConfig`, `QueueService`, or MCP client integration
- the combined FalkorDB container or Neo4j-backed MCP deployment

## Common expectations

- Graphiti defaults to OpenAI for language-model work, so `OPENAI_API_KEY` is
  usually required unless a task explicitly swaps in another client.
- Neo4j and FalkorDB are the main supported graph backends in this repo. Neo4j is
  the default core backend; FalkorDB is the key alternative and the MCP default.
- `GRAPHITI_TELEMETRY_ENABLED=false` keeps the runtime quiet during local checks.
- Kuzu is deprecated and Neptune is a documented but non-default path.

## What this skill does not do

- It does not rewrite the source repository's code or tests.
- It does not depend on the original checkout at runtime; bundled references and
  scripts carry the practical guidance.
- It does not replace the sub-skills when a workflow is clearly about the SDK,
  REST service, or MCP server.

## Provenance and routing metadata

- `references/repo-provenance.md`
- `references/repo-routing-metadata.json`
