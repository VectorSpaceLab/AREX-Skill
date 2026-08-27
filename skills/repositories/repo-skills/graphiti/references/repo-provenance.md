# Repository provenance

## Source

- Repository: Graphiti
- Package/version observed: `graphiti-core` `0.29.3`
- Source commit observed: `425bf24`
- User instruction: create a repo-specific DisCo operating skill for the current
  repository, auto-decide the extraction scope, and do not import it into another
  agent.

## Extraction scope chosen

The skill is split into one root router and three operating sub-skills:

1. `core-sdk` for `graphiti_core`, backends, ingest/search, custom types, and
   provider setup.
2. `rest-service` for the FastAPI service, routes, queue behavior, config, and
   deployment.
3. `mcp-server` for MCP tools, transports, config schema, queueing, and smoke
   checks.

## Evidence anchors used

Primary evidence came from these source areas:

- `README.md`, `pyproject.toml`, `Makefile`, Docker compose files, and test config.
- `graphiti_core/graphiti.py`, drivers, LLM/embedder/cross-encoder clients,
  search recipes, node and edge models, and maintenance helpers.
- `server/graph_service/` app, routers, DTOs, settings, and service tests.
- `mcp_server/src/` server, config schema, service factories, queue service,
  response models, Docker docs, and tests.
- `examples/quickstart/` plus selected provider, tracing, and domain examples.
- Native tests covering SDK mocks, drivers, provider clients, REST, and MCP paths.

Excluded evidence: `.git/`, caches, bytecode, build/generated metadata, and other
non-source artifacts.

## Verification completed

The generated scripts were syntax-checked with Python compilation.

The installed-package smoke check succeeded in the prepared inspection
environment with these installed distribution versions:

- `graphiti-core: 0.29.3`
- `graph-service: 0.1.0`
- `mcp-server: 1.0.2`

The smoke verified imports for:

- `graphiti_core.Graphiti`
- `Neo4jDriver`
- `FalkorDriver`
- `OpenAIClient`
- `OpenAIGenericClient`
- `graph_service.main:app`
- `graphiti_mcp_server.main`

A non-blocking pydantic-settings forward-reference warning appeared while
importing the REST service, matching the previously observed service-import
behavior.

## Verification not completed

Full live workflow verification still requires external services and credentials:

- Neo4j-backed core ingest/search smoke was not run.
- FalkorDB-backed core ingest/search smoke was not run.
- REST live service smoke was not run.
- MCP transport smoke was not run.
- Default real ingest/search still requires `OPENAI_API_KEY` unless a task injects
  custom LLM/embedder/reranker clients.

Bundled scripts provide the follow-up verification path for those live checks.

## Import status

No import/export into another agent was performed, per the user's instruction.
