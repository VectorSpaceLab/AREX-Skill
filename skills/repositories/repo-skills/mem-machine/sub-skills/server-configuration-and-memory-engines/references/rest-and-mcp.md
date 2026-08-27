# REST And MCP

MemMachine exposes REST API v2 for SDK/CLI/client calls and MCP entry points for
tool-style memory operations.

## REST API Families

| Family | Representative paths | Use |
| --- | --- | --- |
| System | `GET /api/v2/health`, `GET /api/v2/metrics` | Readiness and metrics. |
| Projects | `POST /api/v2/projects`, `/projects/get`, `/projects/list`, `/projects/delete`, `/projects/episode_count/get` | Project lifecycle and episode counts. |
| Memories | `POST /api/v2/memories`, `/memories/search`, `/memories/list`, `/memories/episodic/delete`, `/memories/semantic/delete` | Add, search, list, and delete memory. |
| Semantic features | `/memories/semantic/feature`, `/feature/get`, `/feature/update` | Profile/semantic feature CRUD. |
| Semantic sets/categories/tags | `/set_type`, `/set_id`, `/set/configure`, `/category`, `/category/template`, `/category/tag` | Semantic profile organization. |
| Memory config | `/memory/episodic/config`, `/memory/episodic/long_term/config`, `/memory/episodic/short_term/config` | Per-project episodic config. |
| Server config | `/api/v2/config`, `/config/resources`, `/config/memory`, `/config/resources/embedders`, `/config/resources/language_models` | Server-level config when enabled. |

Use the root REST/data-model reference when converting endpoint fields to SDK or
CLI parameters.

## Health And Metrics

```bash
curl -sS "http://localhost:8080/api/v2/health"
curl -sS "http://localhost:8080/api/v2/metrics"
```

Use the actual base URL and auth scheme for the deployment. A health endpoint
success does not prove provider/storage resources are healthy for every memory
workflow.

## MCP Entry Points

```bash
memmachine-mcp-stdio
memmachine-mcp-http --host localhost --port 8080
memmachine-server --stdio
```

MCP context parameters in the inspected source include:

- `org_id`
- `proj_id`
- `user_id`

MCP tool handlers include add/search/delete memory behavior. HTTP mode is for
network-accessible MCP clients; stdio mode is for local clients that launch the
server process directly.

## Choosing HTTP vs Stdio MCP

| Need | Prefer |
| --- | --- |
| Claude Desktop/Cursor-style local process launch | stdio |
| Shared service endpoint or browser/web client | HTTP |
| Existing MemMachine API server already running | HTTP or adapter layer, depending on deployment |
| Simple local smoke without network listener | import/help check only |

Do not start a long-running MCP server as a smoke test unless the user requests
it. Use the bundled `mcp_entrypoint_smoke.py` for import/signature checks.

## Auth And Context

- REST calls may need bearer auth; the Python and TypeScript clients set an
  `Authorization: Bearer ...` header when an API key is supplied.
- MCP tools still need project/user context. If a memory appears to be missing,
  check `org_id`, `proj_id`, `user_id`, and any memory metadata.
- Keep API keys out of MCP config snippets shown in logs; use environment
  variables or secret-manager references.

## Common REST/MCP Failures

- **404**: wrong path prefix (`/v2` vs `/api/v2`) or endpoint disabled.
- **422**: invalid payload fields, wrong memory type, malformed filter, or
  missing required context.
- **500**: backend resource failure, provider error, or server config issue.
- **MCP tool returns empty memory**: wrong project/user context, memory type, or
  search query; compare with a direct REST/CLI search using the same context.
