# Services, FastAPI, and MCP Reference

Read this when you need to start Cognee as a service, inspect the API router
surface, connect or disconnect from Cloud/local instances, or operate the MCP
server and its tools.

## FastAPI service surface

The public API server is started with:

```bash
python -m cognee.api.client
```

Useful startup options and environment hooks:

| Option / env | Meaning | Notes |
| --- | --- | --- |
| `--agent-mode` | Switch the API server to agent mode. | Changes the default port to `8011` instead of `8000`. |
| `HTTP_API_HOST` | Bind host for the API server. | Defaults to `0.0.0.0`. |
| `HTTP_API_PORT` | Bind port for the API server. | Defaults to `8000`, or `8011` in agent mode. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated browser origins allowed by CORS. | If unset, the API defaults to `UI_APP_URL` or `http://localhost:3000`. |
| `UI_APP_URL` | Fallback browser origin for the UI. | Used when `CORS_ALLOWED_ORIGINS` is not set. |

### Router map

The API is split into focused router groups. Read this table when you need the
right prefix or when a user asks about a service surface without remembering the
exact route.

| Router prefix | What it covers |
| --- | --- |
| `/health` | Service liveness and detailed health checks. |
| `/api/v1/checks` | Cloud connection checks. |
| `/api/v1/add`, `/api/v1/cognify`, `/api/v1/search`, `/api/v1/memify` | Core ingest / graph build / query / enrichment workflows. |
| `/api/v1/remember`, `/api/v1/recall`, `/api/v1/improve`, `/api/v1/forget`, `/api/v1/delete`, `/api/v1/update` | Session-memory and graph mutation helpers. |
| `/api/v1/datasets`, `/api/v1/sessions`, `/api/v1/responses`, `/api/v1/settings` | Dataset, session, response, and settings management. |
| `/api/v1/users`, `/api/v1/api_keys`, `/api/v1/permissions` | Auth, identity, API keys, and permission controls. |
| `/api/v1/agents`, `/api/v1/activity`, `/api/v1/skills`, `/api/v1/proposals` | Agents, observability, skills, and proposal surfaces. |
| `/api/v1/visualize`, `/api/v1/schema`, `/api/v1/llm`, `/api/v1/ontologies` | Visualization, schema, prompt, and ontology helpers. |
| `/api/v1/sync`, `/api/v1/integrations`, `/api/v1/slack` | Cloud sync, integration authorizations, and Slack hooks. |

## Cloud / local connection helpers

### `serve`

`cognee.serve()` connects the SDK to a remote or local Cognee instance.

| Mode | How it is chosen | Notes |
| --- | --- | --- |
| Direct / local | Pass `url=` or set `COGNEE_SERVICE_URL`. | Skips Auth0 and tenant discovery. |
| Cloud | Omit `url=` and rely on the cloud flow. | Uses the management API and saved credentials. |

The public helper signature is:

```python
await cognee.serve(url=None, api_key=None, management_url=None, ...)
```

### `disconnect`

`cognee.disconnect(clear_saved=False)` closes the active remote connection and
returns the SDK to local mode. The CLI equivalent is `cognee-cli serve --logout`.

### `push`

`cognee.push()` uploads a local dataset graph to Cognee Cloud without
re-deriving it from raw files.

```python
await cognee.push(
    dataset="main_dataset",
    target_dataset=None,
    mode="preserve",
    run_in_background=False,
    url=None,
    api_key=None,
)
```

Mode summary:

| Mode | Effect |
| --- | --- |
| `preserve` | Import the exported graph directly. |
| `hybrid` | Preserve the graph and also cognify the raw content. |
| `re-derive` | Ignore the exported graph and rebuild from raw content. |

Connection precedence for `push`:

1. Explicit `url` / `api_key` arguments.
2. An active `serve()` connection.
3. `COGNEE_SERVICE_URL` and `COGNEE_API_KEY`.
4. Saved credentials from a previous `serve()` login.

### Dataset sync

Dataset sync is exposed as the API route:

- `POST /api/v1/sync`
- `GET /api/v1/sync/status`

The sync endpoint returns a `run_id` immediately and runs the transfer in the
background.

## MCP server surface

The public MCP entry point supports three transports:

| Transport | Flag | Default | Notes |
| --- | --- | --- | --- |
| `stdio` | `--transport stdio` | Yes | Classic pipe transport. |
| `sse` | `--transport sse` | No | Streaming server-sent events. |
| `http` | `--transport http` | No | Streamable HTTP transport. |

Dependency note: the MCP server is packaged separately from the base CLI surface. A minimal Cognee install may not provide the `cognee-mcp` entry point or the Python `mcp` package; run [scripts/check_mcp_surface.py](../scripts/check_mcp_surface.py) before spending time on client configuration.

Common MCP CLI arguments:

| Argument | Meaning |
| --- | --- |
| `--host` | HTTP bind host. |
| `--port` | HTTP bind port. |
| `--path` | HTTP path for streamable transport. |
| `--log-level` | HTTP server log level. |
| `--no-migration` | Skip database migrations during startup. |
| `--api-url` | Use an already running Cognee FastAPI server instead of local direct mode. |
| `--api-token` | Auth token for API mode. |
| `--serve-url` | Connect the MCP server to Cognee Cloud at startup. |
| `--serve-api-key` | API key for the cloud connection. |

Connection environment mapping:

| Context | Environment variables | Notes |
| --- | --- | --- |
| Direct MCP CLI | `COGNEE_BASE_URL`, `COGNEE_API_KEY` | Used by the MCP entry point when you pass `--api-url` / `--api-token`. |
| Cloud mode | `COGNEE_SERVICE_URL`, `COGNEE_API_KEY` | Used when the server connects to Cognee Cloud. |
| Docker container | `TRANSPORT_MODE`, `HTTP_PORT`, `API_URL`, `API_TOKEN`, `EXTRAS` | These are interpreted by the container entrypoint before `cognee-mcp` starts. |

## MCP tools and resource

The MCP server exposes these tools/resources:

| Tool / resource | What it does | Mode notes |
| --- | --- | --- |
| `remember` | Store data in session cache or permanent memory. | Uses the agent-scoped default dataset when `dataset_name` is omitted. |
| `recall` | Search memory with session-aware routing. | Supports dataset and session filters. |
| `forget` | Delete a dataset or all owned memory. | Requires `dataset` or `everything=true`. |
| `visualize_graph_ui` | Open the graph workspace UI. | Uses resource URI `ui://cognee-visualize/graph.html`. Explicit dataset selection is direct-mode only. |
| `upload_file_ui` | Open the workspace in upload mode. | UI-only helper. |
| `open_cognee_workspace` | Open the generic workspace UI. | UI-only helper. |
| `cognify_file` | Ingest base64 file content and launch cognify in the background. | 10 MB limit; safe for UI uploads. |
| `list_datasets_json` | Return dataset choices for the workspace. | Structured JSON helper. |
| `list_dataset_data_json` | Return dataset item choices for the workspace. | Direct-mode only. |
| `get_client_info_json` | Return the current MCP client identity and default dataset. | Agent-scoped by default. |
| `create_dataset_json` | Create an empty dataset idempotently. | Direct-mode only. |
| `_visualize_graph_ui_resource` | Serve the graph UI HTML bundle. | Fails with a build hint if the bundle is missing. |

### Agent scoping

By default, each MCP client gets its own dataset namespace. The default dataset
name is derived from the client identity and ends in `_memory`.

- Set `COGNEE_MCP_AGENT_SCOPED=false` to fall back to `main_dataset`.
- The workspace helpers use this to keep different agents from sharing memory unintentionally.

### Security and request routing

- `MCP_CORS_ALLOW_ORIGINS` controls which browser origins may talk to the MCP HTTP/SSE app.
- `MCP_ALLOWED_HOSTS` adds host header patterns when binding to non-loopback hosts.
- `MCP_DISABLE_DNS_REBINDING_PROTECTION=true` disables host/origin validation entirely.
- When possible, keep the MCP HTTP app bound to loopback unless you explicitly need LAN access.
- If the UI workspace says the bundle is missing, rebuild the MCP app bundle before retrying.
