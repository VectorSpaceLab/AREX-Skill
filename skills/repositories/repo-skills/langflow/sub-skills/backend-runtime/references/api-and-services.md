# API Routes, Services, and Flow Execution

This reference covers Langflow backend route patterns, router inclusion, request parsing, graph execution, service access, settings behavior, and focused API validation.

## FastAPI Router Topology

Langflow mounts backend APIs under a root `/api` router with versioned subrouters:

- `router_v1` uses prefix `/v1` and includes flow, run, chat, files, projects, variables, users, auth, authz, traces, models, MCP, memory, extension, and other backend route groups.
- `router_v2` uses prefix `/v2` and includes newer files, MCP, registration, and workflow routers.
- The exported router is mounted at `/api`, so a v1 route such as `/flows/` is called as `/api/v1/flows/`.
- Some routes are hidden from OpenAPI with `include_in_schema=False`; they may still be live and must keep auth/permission checks.
- Feature-gated routes should prefer request-time settings/feature checks instead of import-time environment reads when values can come from `--env-file`.

Use the bundled route inspector to confirm prefixes, methods, and hidden route status without depending on the source checkout layout:

```bash
python scripts/inspect_routes.py --module langflow.api.router --router router --include-hidden
```

For a custom module:

```bash
python scripts/inspect_routes.py --module my_package.my_api --router app
```

## Route Handler Pattern

When adding or editing a backend route:

1. Choose the correct router and prefix; most OSS backend REST routes belong under `/api/v1`, while newer contracts may belong under `/api/v2`.
2. Declare authentication with existing dependencies such as active-user, API-key, optional-user, or SSE-specific dependencies.
3. Load the resource in an owner-scoped way by default.
4. If an authorization plugin may grant cross-user access, use a share-aware loader only when the route immediately calls the matching `ensure_*_permission(...)` guard.
5. Return privacy-preserving errors: use `404` for cross-user resource existence privacy and `403` for permission denials only when revealing the resource context is acceptable.
6. Preserve FastAPI response contracts: use `response_model`, `status_code`, and `response_model_exclude_none` intentionally.
7. Convert validation and domain errors to clear `HTTPException` statuses rather than allowing generic `500` responses.

Common focused test signals:

- Malformed bearer tokens return `401`, not `500`.
- Other-user resources return `404` when existence should not be disclosed.
- Validation problems such as bad uploaded flow shape or bad endpoint names return `422`/`400` as appropriate.
- Name or endpoint conflicts return `409`.
- Deployed-flow mutations that violate invariants return `409`.

## Flow Run Endpoints

The simplified run endpoints are the main backend flow-execution path:

- `POST /api/v1/run/{flow_id_or_name}` uses API-key auth.
- `POST /api/v1/run/session/{flow_id_or_name}` uses session auth and is feature-gated.
- `POST /api/v1/run/advanced/{flow_id_or_name}` accepts explicit `inputs`, `outputs`, `tweaks`, `stream`, and `session_id` body fields.
- `POST /api/v1/webhook/{flow_id_or_name}` runs webhook flows in a background task.
- `GET /api/v1/webhook-events/{flow_id_or_name}` streams webhook progress events after a read permission check.

The shared internal run flow path:

1. The route resolves a `Flow`/`FlowRead` for the authenticated caller.
2. The route calls `ensure_flow_permission(..., FlowAction.EXECUTE, flow_id=..., flow_user_id=..., workspace_id=..., folder_id=...)` before execution.
3. `_run_flow_internal` parses the request body if FastAPI could not bind a `SimplifiedAPIRequest` directly.
4. Request headers with the `X-LANGFLOW-GLOBAL-VAR-*` prefix are merged into `context["request_variables"]`.
5. Non-streaming calls generate a `run_id`, call `simple_run_flow`, and schedule telemetry logging as a background task.
6. Streaming calls create an event manager and return a `text/event-stream` `StreamingResponse`; disconnects cancel the graph task.

## JSON and Multipart Parsing

Run requests may arrive as JSON or multipart form data. Preserve the difference:

- JSON bodies are loaded directly into `SimplifiedAPIRequest`.
- Multipart requests call `request.form()` and copy only string-valued fields into the request model.
- Supported multipart fields include `input_value`, `input_type`, `output_type`, `output_component`, `session_id`, and `user_id`.
- Multipart `tweaks` must be a JSON-encoded string or bytes field; if parsing fails, a warning is logged and tweaks are omitted.
- Uploaded file fields are intentionally ignored by the simplified request parser so downstream file handling can still access them.

When diagnosing ignored tweaks, compare the actual `Content-Type` and payload shape:

```bash
curl -X POST "$LANGFLOW_URL/api/v1/run/$FLOW_ID" \
  -H "x-api-key: $LANGFLOW_API_KEY" \
  -H "content-type: application/json" \
  -d '{"input_value":"hello","input_type":"chat","output_type":"chat","tweaks":{"NodeId":{"field":"value"}}}'
```

For multipart, encode `tweaks` as one JSON string field:

```bash
curl -X POST "$LANGFLOW_URL/api/v1/run/$FLOW_ID" \
  -H "x-api-key: $LANGFLOW_API_KEY" \
  -F 'input_value=hello' \
  -F 'input_type=chat' \
  -F 'output_type=chat' \
  -F 'tweaks={"NodeId":{"field":"value"}}'
```

If tweaks work in JSON but not multipart, check that the multipart value is not sent as a file part and is valid JSON.

## `simple_run_flow` Behavior

`simple_run_flow` is the high-level graph execution wrapper used by simplified run and webhook paths. It:

- Rejects conflicting chat/text input when both `input_value` and an input component tweak target the same chat/text input.
- Copies `flow.data` before applying tweaks.
- Applies `process_tweaks(..., stream=stream)` to modify node templates.
- Applies global-variable defaults for authenticated API-key users.
- Builds an `lfx.graph.graph.base.Graph` with flow id, user id, flow name, and optional context.
- Sets `graph.tracing_user_id` from request `user_id` for tracing only; permissions and job ownership still use the authenticated user.
- Creates a workflow job and runs `run_graph_internal` through the job service.
- Fires the memory-base `on_flow_output` hook as a non-blocking task.
- Wraps graph/job failures in API-level exceptions and logs failures.

Do not reintroduce owner-only checks inside `_run_flow_internal`; authorization belongs at the route boundary so plugin-granted execute permissions on shared flows remain possible.

## `process_tweaks` Semantics

`process_tweaks` accepts graph data with either `data.nodes` or top-level `nodes` and a tweaks dictionary.

Key rules:

- Keys matching node ids or node display names apply only to that node.
- Non-dict tweak values are collected and applied to matching fields on every node.
- If no `stream` tweak is supplied, the function injects `stream` based on the route call.
- Code execution fields are protected: code-typed fields, literal `code`, and known code-execution component fields are not overridden by tweaks.
- `NestedDict` fields are repaired/validated as JSON.
- `mcp` fields accept dict values directly.
- Dict fields unwrap a single-key `{ "value": ... }` wrapper.
- File fields use `file_path` as the storage key.
- Tweaking a field with `load_from_db` clears `load_from_db` unless the caller explicitly keeps it.

A tweak that appears ignored may be blocked because the target key does not match a node id/display name, the target field is a protected code field, the field is hidden under a different template name, or multipart parsing dropped the malformed `tweaks` field.

## Services and Dependencies

Langflow backend services are retrieved through dependency helpers backed by the service manager. Use these instead of constructing services directly:

- `get_settings_service()` for settings and auth settings.
- `get_db_service()` and `session_scope()` for database operations.
- `get_auth_service()` for authentication and webhook-user resolution.
- `get_authorization_service()` for plugin capability and enforcement.
- `get_job_service()` for workflow job records and status-managed execution.
- `get_session_service()` for persisted graph sessions.
- `get_task_service()` for fire-and-forget background work.
- `get_memory_base_service()` for memory-base hooks.
- `get_storage_service()`, `get_cache_service()`, `get_telemetry_service()`, and `get_tracing_service()` for their respective concerns.

Service factory registration is lazy. If factories are not registered, the dependency layer registers Langflow service factories before retrieving the service. This means route code should call the helper at request/runtime, not cache service instances at import time unless the service is intentionally process-global.

## Settings and CLI Behavior

Langflow settings are affected by environment variables, `.env` files, and CLI flags.

- Prefer `uv run langflow run` inside a development environment where Langflow is installed.
- CLI options override environment variables and values from the main `.env` file.
- Boolean CLI options typically have both positive and negative forms, such as `--remove-api-keys` and `--no-remove-api-keys`.
- `--env-file` loads a specific environment file, and additional CLI options override duplicate values from that file.
- `--backend-only` starts the backend service without the frontend.
- `--port`, `--host`, `--log-level`, `--worker-timeout`, `--workers`, `--max-file-size-upload`, and `--cache` are common backend options.
- Some route feature flags must be read at request time because the API router may be imported before `--env-file` is loaded.

For local backend work:

```bash
uv run langflow run --backend-only --host localhost --port 7860 --log-level debug
```

## API Test Strategy

Choose focused tests by the behavior changed:

- Flow CRUD, upload validation, user isolation, endpoint-name conflicts, and deployed-flow constraints: `uv run pytest src/backend/tests/unit/api/v1/test_flows.py -q`.
- Share CRUD, OSS owner floor, plugin cross-user behavior, visibility filtering, and invalidation: `uv run pytest src/backend/tests/unit/api/v1/test_authz_share_routes.py -q`.
- Run endpoint parsing/tweaks changes: add or run the nearest run-flow tests and include a multipart case when the bug is form-specific.
- Route listing or mount problems: use `inspect_routes.py` plus the smallest route test that exercises the mounted endpoint.

Avoid broad suites until the focused route and service behavior is correct.
