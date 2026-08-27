# Graphiti workflows

This page gives the quickest practical route into Graphiti's main user-facing
flows. Use it after `installation-and-backends.md` when you already know which
sub-skill owns the task.

## 1) Core SDK quickstart

Use `sub-skills/core-sdk/` when the task is about building or querying a temporal
context graph directly from Python.

Typical flow:

1. Choose a backend driver: `Neo4jDriver` or `FalkorDriver`.
2. Build indices and constraints.
3. Add one episode or a small batch of episodes.
4. Search for facts with `search()` or search for nodes with `search_()`.
5. Optionally build communities, summarize a saga, or inspect provenance.

A small runnable helper lives at `../sub-skills/core-sdk/scripts/quickstart_graphiti.py`. It adds a few
sample episodes and prints both edge search and node-search results. Use it for a
quick environment sanity check or to explain the API to another agent.

Key API surfaces:

- `Graphiti.add_episode(...)`
- `Graphiti.add_episode_bulk(...)`
- `Graphiti.search(...)`
- `Graphiti.search_(...)`
- `Graphiti.retrieve_episodes(...)`
- `Graphiti.build_communities(...)`
- `Graphiti.summarize_saga(...)`
- `Graphiti.add_triplet(...)`

### When to choose the core quickstart

Choose this flow when the user says:

- "ingest episodes"
- "search Graphiti"
- "build a context graph"
- "custom entity types"
- "search recipes"
- "provider setup for Graphiti"

## 2) REST service flow

Use `sub-skills/rest-service/` when the task is about the FastAPI API in
`server/`.

Typical flow:

1. Start the service with the configured backend and credentials.
2. Health-check `/healthcheck`.
3. POST to `/messages` or `/entity-node`.
4. Poll `/episodes/{group_id}` or call `/search` / `/get-memory`.
5. Clean up with `/group/{group_id}` or `/clear` when appropriate.

A bundled smoke helper lives at `../sub-skills/rest-service/scripts/graph_service_smoke.py`. It exercises the
health check, one ingest request, polling for episodes, and a search request.

### When to choose the REST flow

Choose this flow when the user says:

- "REST API"
- "FastAPI service"
- "/messages"
- "/search"
- "/get-memory"
- "healthcheck"
- "service deployment"

## 3) MCP server flow

Use `sub-skills/mcp-server/` when the task is about the MCP transport, tool
catalog, or client integration.

Typical flow:

1. Choose a config file or environment variables.
2. Choose transport: `stdio`, `http`, or `sse`.
3. Start the server.
4. List tools and verify the expected tool names.
5. Call `add_memory`, then `search_nodes` or `search_memory_facts`.
6. Use `get_status` or `clear_graph` for validation and cleanup.

A bundled smoke helper lives at `../sub-skills/mcp-server/scripts/mcp_smoke.py`. It can launch the server
in stdio mode or connect to an already-running HTTP endpoint, then list tools and
run a tiny end-to-end check.

### When to choose the MCP flow

Choose this flow when the user says:

- "MCP"
- "stdio"
- "streamable HTTP"
- "tool catalog"
- "Claude Desktop"
- "Cursor"
- "add_memory"
- "search_nodes"
- "get_status"

## Shared guidance

- Graphiti workflows rely on a live graph backend plus model credentials when the
  workflow performs real ingest or search.
- `group_id` controls graph partitioning. Keep it stable within one workflow and
  use a unique value when you want an isolated smoke run.
- Use the troubleshooting reference when you see import errors, missing backend
  errors, validation errors, or provider fallback problems.
