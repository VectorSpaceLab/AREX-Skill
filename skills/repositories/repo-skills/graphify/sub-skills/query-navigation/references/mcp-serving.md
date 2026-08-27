# Graphify MCP serving

## Purpose

Use this reference when the user wants an assistant or team tool to query an existing Graphify graph through MCP instead of running one-shot CLI commands. Serving does not build a graph; it exposes read tools over stdio or Streamable HTTP.

## Install and preflight

MCP serving is optional. The base Graphify install is enough for CLI query/path/explain, but serving requires the MCP extra:

```bash
python -m pip install "graphifyy[mcp]"
# or the user's isolated-tool manager equivalent
uv tool install "graphifyy[mcp]"

python -m graphify.serve --help
# same entry point when installed as a console script:
graphify-mcp --help
```

If `python -m graphify.serve --help` says `mcp not installed` or `HTTP transport needs the mcp extra`, install `graphifyy[mcp]` in the interpreter that will run the server.

## Stdio server

Stdio is the default transport. Use it for one local MCP client per developer.

```bash
python -m graphify.serve graphify-out/graph.json
python -m graphify.serve --graph graphify-out/graph.json
# equivalent console entry point when installed:
graphify-mcp graphify-out/graph.json
```

MCP client command shape:

```json
{
  "command": "python",
  "args": ["-m", "graphify.serve", "graphify-out/graph.json"]
}
```

Use an absolute graph path when the MCP client starts outside the project directory.

## HTTP server

HTTP uses MCP Streamable HTTP so one process can serve a graph to multiple clients.

```bash
# Local-only default bind.
python -m graphify.serve graphify-out/graph.json --transport http --port 8080

# Shared host: bind externally only with an API key.
GRAPHIFY_API_KEY="$SECRET" \
python -m graphify.serve graphify-out/graph.json \
  --transport http --host 0.0.0.0 --port 8080 --api-key "$GRAPHIFY_API_KEY"
```

HTTP flags:

| Flag | Default | Use |
|---|---|---|
| `--transport stdio|http` | `stdio` | Choose stdio or Streamable HTTP. |
| `--host HOST` | `127.0.0.1` | HTTP bind host. Keep loopback for local use. |
| `--port N` | `8080` | HTTP port. |
| `--api-key KEY` | `GRAPHIFY_API_KEY` | Require `Authorization: Bearer KEY` or `X-API-Key: KEY`. |
| `--path PATH` | `/mcp` | HTTP mount path; clients connect to `http://host:port/path`. |
| `--json-response` | off | Return plain JSON responses instead of SSE streams. |
| `--stateless` | off | Disable per-session state for load-balanced or CI-style use. |
| `--session-timeout N` | `3600` | Reap idle stateful sessions after N seconds; `0` disables. |

Security defaults and requirements:

- `127.0.0.1` is loopback-only and safe for a local developer machine.
- Binding `0.0.0.0`, `::`, or an empty host exposes the graph beyond localhost. Require `--api-key` or `GRAPHIFY_API_KEY` before doing this.
- A blank API key is treated as no auth, not as a valid empty password.
- For authenticated HTTP calls, clients may send either `Authorization: Bearer <key>` or `X-API-Key: <key>`.
- Non-wildcard binds enable Host-header/DNS-rebinding protection. If a test client gets rejected, use the exact host you bound or `localhost`/`127.0.0.1`.
- A graph can contain proprietary labels, file paths, and snippets of user intent. Treat an HTTP MCP endpoint as sensitive even though the tools are graph-read tools.

## Exposed tools

The server exposes graph tools with text responses:

| Tool | Purpose | Important arguments |
|---|---|---|
| `query_graph` | BFS/DFS query over nodes and edges. | `question`, `mode`, `depth`, `token_budget`, `context_filter`. |
| `get_node` | One node by label or ID. | `label`. |
| `get_neighbors` | Direct neighbors with relation/confidence. | `label`, `relation_filter`, `token_budget`. |
| `get_community` | Nodes in a community. | `community_id`, `token_budget`. |
| `god_nodes` | Most-connected graph entities. | `top_n`. |
| `graph_stats` | Node/edge/community and confidence percentages. | none. |
| `shortest_path` | Directed path by default, optional undirected search. | `source`, `target`, `max_hops`, `undirected`. |
| `list_prs`, `get_pr_impact`, `triage_prs` | GitHub PR orientation and graph impact when available. | May need GitHub CLI/network; route PR workflow details to exports/integrations. |

Every tool also accepts optional `project_path`, an absolute project directory containing `graphify-out/graph.json`. Omitting it uses the graph path the server was started with. A shared HTTP server keeps the configured graph pinned and caches a bounded number of project graphs; control the non-default cache size with `GRAPHIFY_MAX_CONTEXTS` (default `8`, minimum `1`).

## Exposed resources

The server may expose these MCP resources from the default graph:

- `graphify://report`: `GRAPH_REPORT.md` when present.
- `graphify://stats`: node, edge, community, and confidence summary.
- `graphify://god-nodes`: top hubs.
- `graphify://surprises`: cross-community surprising connections.
- `graphify://audit`: confidence breakdown.
- `graphify://questions`: suggested graph questions when analysis data is present.

Resources read the server's default graph, not a per-tool `project_path` override.

## Operational checklist

1. Confirm the graph path exists and is the graph the user wants to expose.
2. Confirm the serving interpreter imports `graphify` and has the `mcp` extra.
3. Choose stdio for one local client; choose HTTP only when multiple clients need one shared process.
4. For HTTP, keep `--host 127.0.0.1` unless the user explicitly asks for shared access.
5. Before binding outside localhost, require an API key and prefer `GRAPHIFY_API_KEY` to avoid putting secrets directly in reusable commands.
6. Start the server and verify with a harmless tool such as `graph_stats` or `query_graph` on a known label.
7. If a project-specific tool call fails, check that `project_path/graphify-out/graph.json` exists; a bad project graph should return a tool error without killing the server.

## Safe HTTP exposure hard case

If the user says “serve this graph to the team,” do **not** give only:

```bash
python -m graphify.serve graphify-out/graph.json --transport http --host 0.0.0.0
```

Use the safe form:

```bash
export GRAPHIFY_API_KEY="<generated-secret>"
python -m graphify.serve graphify-out/graph.json \
  --transport http --host 0.0.0.0 --port 8080 --api-key "$GRAPHIFY_API_KEY"
```

Then tell clients to connect to `http://<host>:8080/mcp` with either `Authorization: Bearer <generated-secret>` or `X-API-Key: <generated-secret>`.
