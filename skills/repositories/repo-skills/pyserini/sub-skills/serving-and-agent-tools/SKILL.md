---
name: serving-and-agent-tools
description: "Run and troubleshoot Pyserini REST and MCP servers, server YAML
  configs, OpenAPI clients, API keys, caches, and agent integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving and Agent Tools

Use this sub-skill when a task involves the Pyserini REST server, FastAPI/OpenAPI behavior, MCP server setup, Claude/Cursor MCP configuration, server YAML aliases, API keys, cache sizes, load shedding, server logs, or errors from `pyserini.server.rest` or `pyserini.server.mcp`.

Do not use this sub-skill for building Lucene indexes, interpreting BM25/search semantics, creating dense embeddings, choosing Faiss encoders, package installation, or source checkout resource builds. Route those to `../index-search-fetch/SKILL.md`, `../dense-encoding/SKILL.md`, `../install-and-runtime/SKILL.md`, or `../repo-development/SKILL.md` as appropriate.

## Quick Routing

- **REST server:** Start with `python -m pyserini.server.rest`, add `--config` for aliases/API keys, and read `references/rest-api.md` for endpoints and HTTP parameters.
- **Server YAML:** Validate aliases before startup with `python scripts/validate_server_config.py server.yaml`; read `references/configuration.md` for schema and examples.
- **Locked-down deployment:** Use `--config server.yaml --no-prebuilt-indexes`, configure `api_keys`, tune cache sizes, and use log-file flags.
- **MCP integration:** Use `python -m pyserini.server.mcp` for local stdio clients or `--transport http --port 8000` for remote/forwarded clients; read `references/mcp-server.md`.
- **Troubleshooting:** For invalid aliases, auth failures, missing `faiss`, missing eval jars, stdio-vs-HTTP mismatches, or disabled prebuilt indexes, read `references/troubleshooting.md`.

## Default REST Setup

1. Create a local server config with explicit aliases:

   ```yaml
   indexes:
     local_sparse: ./indexes/demo-lucene
     local_faiss:
       path: ./indexes/demo-faiss
       index_type: faiss
       base_index: local_sparse
       encoder: BAAI/bge-base-en-v1.5
   api_keys:
     - replace-with-a-secret-token
   ```

2. Validate the config without opening indexes:

   ```bash
   python scripts/validate_server_config.py server.yaml
   ```

3. Start the REST server:

   ```bash
   python -m pyserini.server.rest --host 127.0.0.1 --port 8081 --config server.yaml --no-prebuilt-indexes
   ```

4. Search with one of the configured aliases:

   ```bash
   curl -H "Authorization: Bearer replace-with-a-secret-token" \
     "http://127.0.0.1:8081/v1/local_sparse/search?query=information%20retrieval&hits=5"
   ```

## Default MCP Setup

1. For a local stdio MCP client, configure the client to run the same Python executable that imports Pyserini:

   ```json
   {
     "mcpServers": {
       "mcpyserini": {
         "command": "python",
         "args": ["-m", "pyserini.server.mcp", "--config", "server.yaml"]
       }
     }
   }
   ```

2. For a remote or forwarded MCP server, start HTTP transport:

   ```bash
   python -m pyserini.server.mcp --transport http --port 8000 --config server.yaml
   ```

3. Point the MCP client at `http://127.0.0.1:8000/mcp` after forwarding or exposing the port safely.

## What to Read Next

- `references/configuration.md` for the server YAML schema, alias types, API keys, cache flags, and logging flags.
- `references/rest-api.md` for REST endpoints, parameters, response shape, OpenAPI, auth, and status codes.
- `references/mcp-server.md` for MCP transports, client config snippets, tool schemas, and remote setup.
- `references/troubleshooting.md` for config, auth, missing dependency/resource, transport, and prebuilt-index failures.
- `scripts/validate_server_config.py --help` for safe config validation before starting either server.

## Safety Defaults

- Prefer `--no-prebuilt-indexes` with explicit aliases for shared or public deployments so arbitrary local paths and prebuilt downloads are not accepted.
- Use API keys for any network-exposed REST server; both `Authorization: Bearer <token>` and `X-API-Key: <token>` are accepted.
- Treat REST as GET-only and string-query-only; use MCP or direct Pyserini APIs for multimodal queries, `query_generator`, `encoder`, and `ef_search` control.
- Do not run long model downloads or open large indexes while diagnosing server config; validate YAML and imports first.
