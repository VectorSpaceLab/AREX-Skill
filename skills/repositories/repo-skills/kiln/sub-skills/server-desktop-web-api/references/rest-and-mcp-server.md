# REST and MCP server

This reference covers the installable `kiln-server` package: the core FastAPI app, `kiln_server` CLI, and local Kiln MCP server. For desktop-only studio routes, read [desktop-studio-server.md](desktop-studio-server.md). For provider semantics and tool IDs, route to `task-execution-providers-tools`.

## Core REST app

`libs/server/kiln_server/server.py` defines `make_app(lifespan=None, extra_middleware: list[type] | None = None)` and module-level `app = make_app()`.

`make_app` responsibilities:

- Construct `FastAPI(title="Kiln AI API", summary=..., version=_get_version(), lifespan=lifespan, openapi_tags=tags_metadata)`.
- Register `GET /ping` with tag `Settings & Utilities` and `ALLOW_AGENT` metadata.
- Connect the core API modules in this order: projects, tasks, prompts, specs, runs, feedback, documents/RAG, statistics, and shared custom errors.
- Derive browser CORS origins from `KILN_FRONTEND_PORT`, defaulting to the Vite port `5173`.
- Add caller-provided `extra_middleware` first, then `CORSMiddleware`; Starlette makes the last-added middleware outermost, so CORS remains outermost.

Core route ownership:

| Module | Connect function | Main tag(s) | Use for |
| --- | --- | --- | --- |
| `project_api.py` | `connect_project_api(app)` | `Projects` | Project create/list/get/update/import. |
| `task_api.py` | `connect_task_api(app)` | `Tasks` | Task create/list/get/update/delete, rating options, agent-tuned task summaries. |
| `prompt_api.py` | `connect_prompt_api(app)` | `Prompts` | Prompt CRUD and prompt generation from examples. |
| `spec_api.py` | `connect_spec_api(app)` | `Specs` | Eval/spec CRUD for task specs. |
| `run_api.py` | `connect_run_api(app)` | `Runs` | Task run CRUD, bulk upload, execute run, tags. |
| `feedback_api.py` | `connect_feedback_api(app)` | `Feedback` | Feedback CRUD on task runs. |
| `document_api.py` | `connect_document_api(app)` | `Documents` | Documents, extraction, chunking, embedding, vector stores, RAG configs and search. Route detailed RAG semantics to `rag-documents-data`. |
| `statistics_api.py` | `connect_statistics_api(app)` | `Statistics` | Confidence intervals and significance tests. |
| `custom_errors.py` | `connect_custom_errors(app)` | n/a | Uniform JSON error handling. |

`tags_metadata` is the OpenAPI source of truth. When adding a new tag, add it there; when adding a route, use one of the documented tags. Existing tests assert every API route has a tag and every tag is documented and used.

## Running the core server

Installable entry point: `kiln_server = "kiln_server.server:main"`.

Common commands:

```bash
kiln_server --help
kiln_server --host 127.0.0.1 --port 8757 --log-level info
kiln_server --auto-reload
```

CLI behavior:

- `--host` and `--port` are written into `KILN_LOCAL_API_HOST` and `KILN_LOCAL_API_PORT` before `uvicorn.run`, so reload workers see the override.
- Uvicorn target is `kiln_server.server:app`.
- The server reads default host/port from `Config.shared().kiln_local_api_host` and `Config.shared().kiln_local_api_port`.
- `--auto-reload` is useful during server-only development; desktop studio startup has separate entry points.

Safe in-checkout smoke commands:

```bash
uv run kiln_server --help
KILN_SKIP_REMOTE_MODEL_LIST=true uv run python - <<'PY'
from kiln_server.server import make_app
app = make_app()
print(len(app.routes))
print(sorted({tag for route in app.routes for tag in getattr(route, "tags", [])}))
PY
```

The second command imports the app and prints route/tag metadata without binding a socket.

## `connect_*_api` extension pattern

Kiln REST modules generally expose a single `connect_*_api(app: FastAPI)` function and define route-local request/response Pydantic models in the same module.

Endpoint checklist:

1. Choose the owning module; do not add unrelated routes to `server.py` except app-wide plumbing like `/ping`.
2. Add or reuse a documented OpenAPI tag from `tags_metadata`.
3. Use `Path(...)` and `Query(...)` with descriptions for all path/query params.
4. Use Pydantic v2 `BaseModel` response/request models for stable OpenAPI types.
5. Add `openapi_extra`:
   - `ALLOW_AGENT` for safe, intended agent-readable endpoints.
   - `DENY_AGENT` for UI-only, credential, browser-opening, or high-risk routes.
   - `agent_policy_require_approval("...")` for routes agents may call only after user approval.
6. If the endpoint mutates project files and will run under desktop auto Git sync, ensure Git sync locking is correct; see [git-sync-jobs-chat.md](git-sync-jobs-chat.md).
7. If the route appears in the Svelte UI, regenerate/check the OpenAPI schema; see [openapi-and-web-ui.md](openapi-and-web-ui.md).
8. Add targeted tests. Existing route-level tests validate tag coverage, parameter descriptions, CORS, JSON error shape, and schema constraints.

Agent-policy metadata comes from `kiln_server.utils.agent_checks.policy` and appears in OpenAPI as `x-agent-policy`.

## CORS and middleware

`kiln_server.make_app(extra_middleware=[...])` exists so desktop can install middleware inner to CORS. Do not replace it with direct `app.add_middleware` after the app is returned if the middleware can short-circuit responses; doing so can bypass CORS headers and cause browser `origin not allowed` failures.

Allowed frontend origins are limited to loopback `localhost` and `127.0.0.1` for the configured frontend port over HTTP and HTTPS.

## Custom errors

`connect_custom_errors(app)` installs exception handlers for Pydantic validation, FastAPI request validation, `HTTPException`, `KilnRunError`, `httpx.TimeoutException`, and general exceptions. Match the existing JSON shape when adding special handlers so the web UI can read `message` consistently.

## MCP server CLI

Installable entry point: `kiln_mcp = "kiln_server.mcp.mcp:main"`.

The MCP server exposes eligible project tools, including RAG/search tools and Kiln task tools, to an MCP client. It is intended for local usage, not production multi-tenant serving.

Common commands:

```bash
kiln_mcp --help
kiln_mcp --list-tools /path/to/project.kiln
kiln_mcp --transport stdio /path/to/project.kiln
kiln_mcp --transport streamable-http --host 127.0.0.1 --port 8000 /path/to/project.kiln
kiln_mcp --transport sse --mount-path /mcp --tool-ids rag::RAG_ID,kiln_task::TASK_TOOL_ID /path/to/project.kiln
```

CLI behavior from `mcp/mcp.py`:

- Positional `project` must exist and be a file.
- `--tool-ids` is comma-separated; omitted means expose all eligible project tools.
- `--list-tools` prints active RAG and Kiln task tool IDs and skips archived tools.
- `--transport` supports `stdio`, `sse`, and `streamable-http`; network transports accept host, port, mount path, and log level.
- Startup loads `Project.load_from_file`, resolves tools with `collect_project_tools`, prepares runtime contexts with `prepare_tool_contexts`, creates a FastMCP server, and runs the selected transport.

MCP gotchas:

- Search/RAG tools require indexing to have already run for the same project on the same machine.
- Current tool imports require a lock-compatible `mcp` version at the 1.10.1 level; if imports fail after dependency resolution, check the installed `mcp` package first.
- RAG tool exposure can trip optional vector-store imports. LanceDB-related imports require `pandas` in the active environment.
- Remote/local MCP connectivity and provider-backed Kiln task tools can need credentials or running services. Treat those as optional service checks unless the user explicitly asks to validate them.

## Evidence notes

Evidence came from `libs/server/README.md`, `libs/server/pyproject.toml`, `libs/server/kiln_server/server.py`, `libs/server/kiln_server/utils/agent_checks/policy.py`, `libs/server/kiln_server/git_sync_decorators.py`, `libs/server/kiln_server/mcp/README.md`, `libs/server/kiln_server/mcp/mcp.py`, and server tests for CORS/OpenAPI/tag invariants. Verified package evidence covered `kiln-server` 1.0.4 and the `kiln_server` / `kiln_mcp` CLI entry points.
