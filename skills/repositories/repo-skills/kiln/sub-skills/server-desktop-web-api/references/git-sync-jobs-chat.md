# Git sync, jobs, chat, and agent APIs

This reference covers cross-cutting desktop server APIs where request lifecycle, streaming behavior, credentials, and UI state matter.

## Git sync middleware

`app/desktop/git_sync/middleware.py` defines `GitSyncMiddleware`, installed through `kiln_server.make_app(extra_middleware=[GitSyncMiddleware])`. This keeps it inner to CORS so short-circuit error responses still receive CORS headers on the way out.

Core behavior:

- Only HTTP requests are inspected; non-HTTP scopes pass through.
- Project-scoped routes are matched by `^/api/projects/([^/]+)`.
- The project ID is resolved to a project path and Git sync config. Only `sync_mode == "auto"` with a clone path creates a manager.
- Non-mutating reads call `manager.ensure_fresh_for_read()` and notify background sync.
- Mutating methods (`POST`, `PUT`, `PATCH`, `DELETE`) and endpoints decorated with `@write_lock` run inside `manager.atomic_write(...)`.
- Responses under a write lock are buffered so commit/push can happen before the response returns.
- If a write-locked response is `text/event-stream`, middleware returns a 500 advising `@no_write_lock`; streaming under a buffered write lock is a bug.
- Dev mode can detect dirty repos after unlocked requests and report missing lock coverage.

Use these decorators from `kiln_server.git_sync_decorators`:

- `@write_lock`: for `GET` endpoints that mutate project files.
- `@no_write_lock`: for mutating or streaming endpoints that must bypass the write lock and manage their own save/commit behavior.
- `build_save_context(request)`: for `@no_write_lock` endpoints that need to pass a Git-aware atomic write factory down into lower-level runners.

CORS/order rule: do not add `GitSyncMiddleware` directly to the returned app after CORS. Keep the `extra_middleware` pattern so CORS remains outermost.

## Git sync REST APIs

`app/desktop/git_sync/git_sync_api.py` exposes setup and config routes tagged `Git Sync`:

- `POST /api/git_sync/test_access`: test remote read/auth and detected auth mode.
- `POST /api/git_sync/list_branches`: list remote branches/default branch.
- `POST /api/git_sync/clone`: clone into a temporary project-directory path.
- `POST /api/git_sync/test_write_access`: test push/write access from a clone path.
- `POST /api/git_sync/scan_projects`: find `.kiln` projects in a clone.
- `POST /api/git_sync/rename_clone`: move temp clone to final `.git-projects` location.
- `POST /api/git_sync/save_config`: save project Git sync config and register the project.
- `GET/PATCH/DELETE /api/git_sync/config/{project_id}`: read/update/delete config with tokens redacted on read.
- `POST /api/git_sync/oauth/start`, `GET /api/git_sync/oauth/callback`, `GET /api/git_sync/oauth/authorize`, `GET /api/git_sync/oauth/status/{state}`: GitHub OAuth/App install flow.
- `DELETE /api/delete_project/{project_id}`: intentionally outside `/api/projects/*`; removes the project from Kiln config without Git operations so stale credentials do not block deletion.

Security/validation details:

- Clone paths are validated under the default project directory.
- Saved project paths must be relative and must not escape the clone root.
- PAT/OAuth tokens are redacted in config responses.
- OAuth pages are rendered as simple HTML and are `DENY_AGENT`.
- Remote Git calls are network/service operations; do not run them during safe inspection.

## Jobs API and registry

`app/desktop/studio_server/jobs/api.py` connects routes tagged `Jobs`. `connect_jobs_api(app)` registers available workers each time it is called; repeated `make_app()` calls are safe because `register_type` overwrites by type name.

Routes:

- `GET /api/jobs/events`: SSE stream; filters by `job_id`, `type`, and `project_id`.
- `GET /api/jobs`: list jobs with optional status/type/project/since/limit filters.
- `POST /api/jobs/{type}`: create a registered job; optional `wait=true` and `timeout` can return the final record.
- `GET /api/jobs/{id}`: get/reconcile a job.
- `GET /api/jobs/{id}/result`: return result only after success.
- `GET /api/jobs/{id}/wait`: wait for terminal state; disconnect cancels the waiter only, not the job.
- `GET /api/jobs/{id}/errors`: best-effort per-run error log; always returns a list.
- `POST /api/jobs/{id}/pause`, `/resume`, `/cancel`, and `DELETE /api/jobs/{id}`: lifecycle mutation with explicit agent approval policy.

Registry model:

- Jobs are in-memory only and are not persisted.
- IDs look like `j_` plus a random base32-ish suffix.
- Default concurrency is 10; `KILN_JOBS_MAX_CONCURRENT` can override with a positive integer.
- Statuses are `pending`, `running`, `paused`, `succeeded`, `failed`, and `cancelled`.
- Terminal statuses are `succeeded`, `failed`, and `cancelled`.
- `JobContext.report_progress` emits generic count progress.
- `JobContext.report_progress_detail` stamps typed per-worker progress and validates it against `worker.progress_model`.
- `JobContext.report_error` appends structured non-fatal errors to the current run's error log.
- A real worker should implement idempotent `run()` and pure-read `compute_state()` so pause/resume/reconciliation can recover true progress from source-of-truth entities.

SSE caveats:

- `GET /api/jobs/events` is a pure observer. Disconnecting or closing the response unsubscribes only; it never cancels the job.
- The stream emits an initial `snapshot`, then `job`, `deleted`, and keepalive ping comments.
- The event bus owns its keepalive timeout inside the async generator; wrapping `__anext__()` externally with `wait_for` would finalize the generator after one timeout.
- Desktop lifespan calls `job_registry.events.shutdown()` so open SSE subscribers exit promptly on server shutdown without touching running jobs.

When adding a new job type:

1. Create a `JobWorker` subclass with `type_name`, `params_model`, `result_model`, optional `progress_model`, and `supports_pause` if applicable.
2. Make `compute_state()` a side-effect-free read from true backing entities.
3. Make `run()` idempotent; resuming calls `run()` again after `compute_state()`.
4. Register the worker in `connect_jobs_api` or an adjacent registry setup function.
5. Add server tests for create/list/wait/result/errors/events/lifecycle as relevant.
6. Add Svelte store/component tests if the UI renders the progress detail.

## Chat and Copilot stream APIs

`app/desktop/studio_server/chat/routes.py` connects chat routes tagged `Copilot`. These proxy Kiln Copilot upstream APIs and local tool execution.

Routes:

- `POST /api/chat`: forwards messages to upstream chat and streams AI SDK events as SSE.
- `POST /api/chat/execute-tools`: executes user-approved client tools, emits tool execution events, then continues upstream chat.
- `GET /api/chat/version_policy`: fetches upgrade policy; upstream failures degrade to no banner.
- `GET /api/chat/sessions`: list chat sessions.
- `GET /api/chat/sessions/{session_id}`: get a chat session snapshot.
- `DELETE /api/chat/sessions/{session_id}`: delete a chat session.

Chat stream behavior:

- `ChatStreamSession.stream()` forwards upstream `data:` lines and parses AI SDK tool-input events.
- Client-executed tools can be executed locally by mapping function names to Kiln built-in tool IDs; unknown tools return a JSON error string rather than raising.
- Tools marked as server-executed are skipped locally.
- Approval-required client tool calls produce a `tool-calls-pending` SSE payload and stop the stream until the UI posts decisions.
- Tool continuations are formatted in OpenAI-compatible assistant/tool message form.
- `MAX_TOOL_ROUNDS` prevents infinite tool loops and returns an error SSE when exhausted.
- `RemoteProtocolError` is handled specially: expected close after tool-call boundary is debug-logged; unexpected close yields a generic error event with trace ID.

Credential caveat: chat and Copilot routes require a Kiln Copilot API key and upstream service. Treat them as optional unless the user explicitly asks to validate Copilot and provides working credentials/service access.

## Agent overview endpoint

`app/desktop/studio_server/agent_api.py` defines `GET /api/projects/{project_id}/tasks/{task_id}/agent_overview` with tag `Agent` and `ALLOW_AGENT`.

It returns a token-efficient task overview:

- Project and task metadata, including JSON schemas and truncated instruction.
- Dataset counts by tag, source, and rating.
- Document counts by tag and kind.
- Active RAG/search tools and archived count.
- Prompt summaries, including generated prompt count.
- Spec/eval summaries and run-config summaries.
- Tool servers, fine-tune count, prompt optimization job count, project skills, and connected providers.

Use it for UI/agent context summaries, not as a replacement for core datamodel APIs when exact object persistence or mutation is required.

## Provider, tool, skill, import, and settings APIs

The desktop server includes several UI-facing route families:

- Provider/model settings and connection probes live in `provider_api.py`; avoid calling paid/cloud/Ollama/Docker Model Runner checks unless asked.
- Tool server management lives in `tool_api.py`; route tool ID semantics and execution behavior to `task-execution-providers-tools`.
- Project skill CRUD lives in `skill_api.py`; skill file/datamodel semantics route to `project-datamodel`.
- File picker/import and settings/open-folder routes are UI-local and often `DENY_AGENT`.

When adding or changing these routes, update OpenAPI and web wrappers as described in [openapi-and-web-ui.md](openapi-and-web-ui.md).

## Evidence notes

Evidence came from `app/desktop/git_sync/middleware.py`, `app/desktop/git_sync/git_sync_api.py`, `libs/server/kiln_server/git_sync_decorators.py`, `app/desktop/studio_server/jobs/api.py`, `app/desktop/studio_server/jobs/registry.py`, `app/desktop/studio_server/jobs/events.py`, `app/desktop/studio_server/jobs/models.py`, `app/desktop/studio_server/chat/routes.py`, `app/desktop/studio_server/chat/stream_session.py`, `app/desktop/studio_server/agent_api.py`, `app/desktop/studio_server/provider_api.py`, `app/desktop/studio_server/tool_api.py`, `app/desktop/studio_server/skill_api.py`, and corresponding tests.
