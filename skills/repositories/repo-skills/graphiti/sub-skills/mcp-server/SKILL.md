---
name: mcp-server
description: "Guides Graphiti MCP tools, transports, config, and smoke checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# mcp-server

Use this sub-skill for the Graphiti MCP server in `mcp_server/`: tool names,
transport selection, config files, custom entity and edge types, Docker images,
and client-level smoke checks.

## Read first

- `references/mcp-tools.md` for the verified tool catalog and payload shapes.
- `references/configuration.md` for YAML settings, CLI overrides, transports, and
  backend/provider selection.
- `references/troubleshooting.md` when the server fails to start, tool calls return
  errors, or a client is pointed at the wrong transport or backend.
- `scripts/mcp_smoke.py` for a bundled tool-listing and tiny end-to-end smoke.

## What belongs here

Use this sub-skill when the task mentions:

- `graphiti_mcp_server`, `main.py`, `FastMCP`, `mcp`, `stdio`, `http`, or `sse`
- `add_memory`, `search_nodes`, `search_memory_facts`, `get_episodes`, `get_status`,
  `clear_graph`, `summarize_saga`, `build_communities`, `add_triplet`, or
  `get_episode_entities`
- `config.yaml`, `GraphitiConfig`, `QueueService`, `entity_types`, `edge_types`, or
  `edge_type_map`
- Docker Compose for the combined FalkorDB container or the Neo4j container path
- Cursor or Claude Desktop MCP integration questions

## What does not belong here

Route these elsewhere:

- Direct Graphiti SDK questions -> `sub-skills/core-sdk/`
- REST route questions and FastAPI deployment -> `sub-skills/rest-service/`
- Repo maintenance, provenance, or package import details -> root references

## MCP workflow

1. Choose a backend and model configuration.
2. Choose a transport: `stdio`, `http`, or `sse`.
3. Start the server.
4. List tools to confirm the expected catalog.
5. Use `add_memory` or `add_triplet` to write data.
6. Search with `search_nodes` or `search_memory_facts`.
7. Validate with `get_status` and clean up with `clear_graph` if needed.

## Tool families

- Memory ingest: `add_memory`, `add_triplet`
- Search: `search_nodes`, `search_memory_facts`
- Retrieval and provenance: `get_episodes`, `get_entity_edge`, `get_episode_entities`
- Maintenance: `delete_episode`, `delete_entity_edge`, `clear_graph`, `build_communities`, `summarize_saga`
- Diagnostics: `get_status`, `/health`

## Validation path

For a local stdio smoke:

```bash
python scripts/mcp_smoke.py --transport stdio
```

For an HTTP smoke against an already running server:

```bash
python scripts/mcp_smoke.py --transport http --base-url http://127.0.0.1:8000
```
