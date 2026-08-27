# Troubleshooting server, desktop, web API

Use this reference when server imports, route inspection, schema generation, web API calls, Git sync, jobs/SSE, chat, MCP, or optional services fail.

## FastAPI app import fails

Symptoms:

- `ModuleNotFoundError: kiln_ai` or `ModuleNotFoundError: kiln_server`.
- `ImportError` while importing `app.desktop.desktop_server.make_app`.
- Schema generation fails before writing `api_schema.d.ts`.

Checks:

```bash
uv run python - <<'PY'
import kiln_ai, kiln_server
print("kiln packages import")
PY
uv run python scripts/inspect_kiln_server.py --app server --summary
uv run python scripts/inspect_kiln_server.py --app desktop --repo-root "$KILN_REPO_ROOT" --summary
```

Fixes:

- Run from a Kiln checkout with the workspace environment available, or install the package distributions that match the checkout.
- Verified distribution evidence used `kiln-ai`, `kiln-server`, and `kiln-studio-desktop` 1.0.4.
- For schema/import checks, set or preserve `KILN_SKIP_REMOTE_MODEL_LIST=true` so app import does not start optional remote model-list refresh.
- If an optional RAG/vector-store import fails on LanceDB-related modules, ensure `pandas` is installed in the active environment.

## Starlette/FastAPI version incompatibility

Symptoms:

- Runtime or test failures inside Starlette middleware/static file internals.
- CORS, webhost, TestClient, or middleware behavior differs unexpectedly.

Known version evidence:

- Starlette 1.6 is incompatible with the current server code.
- Starlette 0.52.1 worked in the verified environment.
- The root workspace pins a safe minimum through dependency overrides; do not loosen it casually.

Fixes:

```bash
uv run python - <<'PY'
import fastapi, starlette
print("fastapi", fastapi.__version__)
print("starlette", starlette.__version__)
PY
```

If the Starlette version is outside the compatible range, resolve dependencies through the Kiln workspace rather than manually upgrading transitive packages.

## Route count or tags look wrong

Symptoms:

- `inspect_kiln_server.py` reports fewer routes than expected.
- OpenAPI tag tests fail.
- A desktop-only route is missing.

Checks:

```bash
python scripts/inspect_kiln_server.py --app server --list-routes
python scripts/inspect_kiln_server.py --app desktop --repo-root "$KILN_REPO_ROOT" --list-routes
```

Interpretation:

- Core `server` app includes `/ping` and core package REST APIs.
- `desktop` app includes core routes plus provider/settings/import/tool/skill/eval/fine-tune/synthetic-data/prompt-optimization/Copilot/Git-sync/agent/chat/jobs/webhost routes.
- Verified desktop package evidence registered 83 routes; route count may change when source changes, but a sudden drop usually means an import failed or the wrong app was inspected.

Fixes:

- Use `app.desktop.desktop_server.make_app()` for studio routes.
- Ensure `connect_webhost(app)` is last; it should not hide already-registered API routes.
- Add every new route's tag to `tags_metadata` or use an existing tag.
- Add descriptions to every `Path` and `Query` parameter.

## CORS or browser says origin not allowed

Symptoms:

- Browser blocks Git sync or API error responses even though the route returned JSON.
- Response lacks `access-control-allow-origin` for loopback Vite origin.

Checks:

```bash
KILN_FRONTEND_PORT=5173 python - <<'PY'
from kiln_server.server import make_app
app = make_app()
print(app.user_middleware)
PY
```

Fixes:

- Keep CORS outermost by adding short-circuiting middleware through `kiln_server.make_app(extra_middleware=[...])` before CORS is added.
- Do not call `app.add_middleware(GitSyncMiddleware)` after app construction.
- Confirm the frontend origin is loopback and uses `KILN_FRONTEND_PORT` when not on `5173`.

## API path returns HTML instead of JSON

Symptoms:

- A missing `/api/...` route returns the web app's `404.html`.
- The UI receives HTML when it expects JSON `{ "message": ... }`.

Fixes:

- Ensure API routes begin with `/api` when they are API endpoints.
- Ensure `connect_webhost(app)` is registered after every API route.
- Check `HTMLStaticFiles.get_response` still guards `GET` and `HEAD` `/api` paths.
- Keep the 404 handler's API branch returning JSON for `StarletteHTTPException`.

## OpenAPI schema is stale

Symptoms:

- TypeScript says an endpoint path or schema field does not exist.
- `check_schema.sh` prints a diff.
- Web tests pass against hand-written types but fail against generated types.

Fixes:

```bash
bash scripts/check_openapi_schema.sh --check
bash scripts/check_openapi_schema.sh --generate
```

If direct schema generation fails, try fetching from a running server:

```bash
KILN_PORT=8757 app/web_ui/src/lib/check_schema.sh
```

Always regenerate after changing route paths, request/response Pydantic models, field constraints, tags, or path/query params used by the web UI.

## Git sync write-lock problems

Symptoms:

- Streaming endpoint returns an internal error about missing `@no_write_lock`.
- Dev mode reports a dirty repo after an unlocked request.
- Auto-sync project writes are not committed/pushed.
- Browser receives Git sync errors without CORS headers.

Fixes:

- Project-file writes should usually live under `/api/projects/{project_id}/...` so middleware can resolve the project.
- Mutating methods are locked automatically unless decorated with `@no_write_lock`.
- Add `@write_lock` to mutating `GET` endpoints.
- Add `@no_write_lock` to SSE/long-running endpoints and pass `build_save_context(request)` to lower-level writers when needed.
- Keep Git sync middleware inner to CORS via `extra_middleware`.
- Do not perform safe inspection against real remotes; Git sync setup endpoints call network services.

## Jobs/SSE stream problems

Symptoms:

- Job stream disconnect appears to cancel a job.
- Open SSE keeps dev-server reload from completing.
- EventSource reconnect loops or never receives initial state.
- Lifecycle endpoints return 409.

Checks:

- `GET /api/jobs/events` should emit an initial `snapshot` event.
- Client should listen for named `snapshot`, `job`, and `deleted` events.
- Keepalive pings are comments (`: ping`) and should not be parsed as JSON.
- Lifecycle mutation status 409 means invalid transition, unsupported pause, or deletion of non-terminal job.

Fixes:

- Ensure SSE uses `CancellableStreamingResponse` and the registry event bus, not direct job task ownership.
- Do not cancel worker tasks when an observer disconnects.
- On shutdown, call `job_registry.events.shutdown()` to close subscriptions promptly.
- Make new workers' `compute_state()` pure-read and `run()` idempotent so resume/reconcile are safe.
- Bound concurrency with `KILN_JOBS_MAX_CONCURRENT` only when needed.

## Chat/Copilot stream problems

Symptoms:

- `/api/chat` returns an error SSE or fails immediately.
- Tool approval flow stalls.
- Session list/get/delete proxies fail.
- Version policy endpoint always returns no banner.

Likely causes:

- Missing or invalid Kiln Copilot API key.
- Upstream Copilot service unavailable.
- Client tool metadata missing approval/executor fields.
- Upstream closed after a tool-call boundary; this can be expected and should not be double-reported.

Fixes:

- Validate Copilot credentials only when the user asks; this is an optional service path.
- Preserve the `tool-calls-pending` flow for approval-required tools.
- Keep local tool execution mapped through known function-name to tool-ID mapping.
- Unknown tool names should produce a JSON error string result, not crash the stream.

## MCP server problems

Symptoms:

- `kiln_mcp` import or startup fails.
- No tools are exposed.
- RAG/search tool fails despite project loading.

Fixes:

```bash
kiln_mcp --help
kiln_mcp --list-tools /path/to/project.kiln
```

- Ensure the active environment has a lock-compatible `mcp` package at the 1.10.1 level.
- Ensure the project file exists and is a file.
- Omit `--tool-ids` to see all eligible non-archived tools, then narrow.
- RAG/search tools require indexing to have already run for that project on the same machine.
- LanceDB/vector-store imports can require `pandas`.
- Remote/local MCP servers and provider-backed task tools can require credentials or running services.

## Provider, Ollama, cloud, and paid-service problems

Symptoms:

- Provider connection routes return 401/403/417/500.
- Ollama or Docker Model Runner routes say the service is unavailable.
- Paid tests or Copilot flows fail without credentials.

Fixes:

- Treat these as optional unless the task explicitly requires provider/service validation.
- Do not run provider connection probes during safe import/schema inspection.
- For Ollama, ensure the local Ollama app is running and has at least one supported model installed.
- For cloud providers, verify API keys through the UI/API route only with user approval.
- Route model/provider registry and execution semantics to `task-execution-providers-tools`.

## Web UI API/state problems

Symptoms:

- A store compiles but component tests fail.
- EventSource state leaks across project switches.
- Tool/skill/run-config selectors show stale or duplicated data.

Fixes:

- Use generated `components["schemas"]` and `paths` types from `api_schema.d.ts`.
- Keep API wrappers in stores or `$lib/...` helpers, not embedded in components.
- For EventSource stores, close the old source before opening a new one and ignore stale callbacks from old sources.
- Add focused Vitest tests for reconnection, project changes, deletion events, and error states.
- Route UI visual design, accessibility, formatting, and broad web command policy to `repo-development`.

## Evidence notes

Evidence came from server, desktop, Git sync, jobs, chat, webhost, OpenAPI schema scripts, web stores/tests, and verified environment gotchas: `mcp` compatibility at 1.10.1, Starlette 1.6 incompatibility with Starlette 0.52.1 working, LanceDB requiring `pandas`, and optional paid/provider/Ollama/cloud/Copilot flows needing credentials or services.
