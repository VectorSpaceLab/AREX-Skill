# Desktop studio server

This reference covers the desktop server that wraps `kiln_server.make_app()` with studio-only APIs, Git sync middleware, jobs, chat, and static web hosting.

## Desktop app construction

`app/desktop/desktop_server.py` defines `make_app(tk_root: tk.Tk | None = None)`.

Construction sequence:

1. `setup_litellm_logging()` configures LiteLLM logging.
2. Unless remote model-list refresh is skipped, `refresh_model_list_background()` starts model-list refresh in the background.
3. `kiln_server.make_app(lifespan=lifespan, extra_middleware=[GitSyncMiddleware])` builds the core REST app and installs Git sync middleware inner to CORS.
4. Studio extensions are connected: providers, prompt generation, repair, settings, synthetic data, fine-tuning, evals, run configs, import, tool servers, skills, prompt optimization, Copilot, batch plan, Git sync, agent overview, dev tools, chat, and jobs.
5. `connect_webhost(app)` is called last because it mounts `/` as a catch-all for the built Svelte app.

Use the core app (`kiln_server.make_app`) when you only need package server routes. Use the desktop app (`app.desktop.desktop_server.make_app`) when you need provider/settings/forms, jobs, chat, Git sync, or the web UI.

## Lifespan behavior

The desktop lifespan function:

- Enables asyncio event-loop debug when `DEBUG_EVENT_LOOP=true`.
- Forces datamodel strict mode on startup and restores the previous setting on shutdown.
- Starts background Git sync for configured auto-sync projects whose clone paths exist.
- On shutdown, calls `job_registry.events.shutdown()` so open jobs SSE streams stop blocking dev-server reloads; this does not cancel jobs.
- Stops all registered background syncs and closes Git sync managers.

When testing app startup, patch remote model-list refresh or set the skip environment variable so imports do not make optional service calls.

## Studio route modules

Studio route ownership:

| Module | Connect function | Main tag(s) | Notes |
| --- | --- | --- | --- |
| `provider_api.py` | `connect_provider_api(app)` | `Providers & Models` | Provider/model listings, Ollama/Docker Model Runner checks, API-key connect/disconnect, Kiln Copilot API key. Provider semantics route to `task-execution-providers-tools`. |
| `prompt_api.py` | `connect_prompt_api(app)` | `Prompts` | Desktop prompt generation endpoint. |
| `repair_api.py` | `connect_repair_api(app)` | `Runs` | Generate/save repairs for run output. |
| `settings_api.py` | `connect_settings(app)` | `Settings & Utilities` | Settings read/update, open logs/project folder, entitlement check. |
| `data_gen_api.py` | `connect_data_gen_api(app)` | `Synthetic Data` | Categories, sample generation, data guide jobs and refinement. |
| `finetune_api.py` | `connect_fine_tune_api(app)` | `Fine-tuning` | Dataset splits, fine-tune CRUD, provider/hyperparameter listings, JSONL download. |
| `eval_api.py` | `connect_evals_api(app)` | `Evals`, `Run Configs` | Evals, eval configs, calibration/progress/results/score summaries, task run configs. |
| `run_config_api.py` | `connect_run_config_api(app)` | `Run Configs`, `Tasks` | Input-transform validation, MCP run-config creation, task-from-tool creation. |
| `import_api.py` | `connect_import_api(app, tk_root=...)` | `Settings & Utilities` | Native file picker for selecting `.kiln` files; UI/browser-only behavior. |
| `tool_api.py` | `connect_tool_servers_api(app)` | `Tools & MCP` | Tool server CRUD, available tool sets, demo tools, search tools, tool definitions. |
| `skill_api.py` | `connect_skill_api(app)` | `Skills` | Project skill list/content/create/archive/open folder. |
| `prompt_optimization_job_api.py` | `connect_prompt_optimization_job_api(app)` | `Prompt Optimization` | Prompt optimization job checks/start/status/result. |
| `copilot_api.py` | `connect_copilot_api(app)` | `Copilot` | Spec/data Copilot actions. Requires Copilot credentials/service. |
| `batch_plan_api.py` | `connect_batch_plan_api(app)` | `Copilot` | Copilot batch planning. |
| `git_sync_api.py` | `connect_git_sync_api(app)` | `Git Sync`, `Projects` | Git import, OAuth, config, project delete. See [git-sync-jobs-chat.md](git-sync-jobs-chat.md). |
| `agent_api.py` | `connect_agent_api(app)` | `Agent` | Token-efficient task overview for Kiln chat agent. |
| `dev_tools.py` | `connect_dev_tools(app)` | hidden | `/scalar`, excluded from OpenAPI. |
| `chat/routes.py` | `connect_chat_api(app)` | `Copilot` | Chat SSE proxy and tool-approval continuation. See [git-sync-jobs-chat.md](git-sync-jobs-chat.md). |
| `jobs/api.py` | `connect_jobs_api(app)` | `Jobs` | Background jobs and job SSE. See [git-sync-jobs-chat.md](git-sync-jobs-chat.md). |
| `webhost.py` | `connect_webhost(app)` | n/a | Static web UI catch-all; must be last. |

## Desktop server startup helpers

`server_config(port, host, tk_root=None)` returns a `uvicorn.Config` for `make_app(tk_root=tk_root)`.

`ThreadedServer` subclasses `uvicorn.Server` and provides `run_in_thread()` for desktop integration:

- It disables signal handlers, starts uvicorn in a daemon thread, waits until started or stopped, and then asks the server to exit on context teardown.
- `DesktopServer` in `app/desktop/desktop.py` extends this to quit the Tk/tray app when the server stops.

Use `server_config` plus `ThreadedServer` when exercising the real desktop/studio server. For route inspection and tests, prefer importing `make_app()` directly without starting uvicorn.

## Webhost catch-all

`app/desktop/studio_server/webhost.py` mounts static files at `/` using `HTMLStaticFiles(directory=studio_path(), html=True)`. This must happen after all API routes are registered.

Key webhost behavior:

- Explicit MIME types are added for CSS, JavaScript, HTML, SVG, PNG, and JPEG to avoid platform-specific registry issues.
- `HTMLStaticFiles.get_response` refuses to serve web-app content for `GET`/`HEAD` `/api` paths; unmatched API paths remain JSON 404s.
- Non-API paths get the SPA/static fallback, including `.html` fallback.
- Static responses get no-cache headers to prevent an old web app from calling new APIs after upgrade.
- The 404 exception handler returns JSON `{ "message": ... }` for API paths and serves the web app's `404.html` for non-API paths.

If API routes appear to return HTML, first check that `connect_webhost(app)` is last and that API paths are under `/api`.

## Endpoint extension checklist

When adding a desktop/studio endpoint:

1. Pick the narrowest route module and tag. Add to `tags_metadata` only if the tag is truly new.
2. Decide agent policy:
   - Safe summary/list/read endpoints can use `ALLOW_AGENT`.
   - Browser-opening, credential, OAuth, file-picker, UI-only, or secret-revealing endpoints should use `DENY_AGENT`.
   - Agent-allowed mutation should use `agent_policy_require_approval` with a clear user-facing approval string.
3. If the endpoint writes project files under auto Git sync, place it under `/api/projects/{project_id}/...` unless it intentionally only updates app config. See [git-sync-jobs-chat.md](git-sync-jobs-chat.md).
4. For SSE/streaming endpoints, use `CancellableStreamingResponse` and `@no_write_lock` if project-scoped.
5. Use Pydantic models with `Field(description=...)` and `Path`/`Query` descriptions. Existing tests enforce parameter descriptions and OpenAPI string constraints.
6. Update `app/web_ui/src/lib/api_schema.d.ts` via the schema flow before using the endpoint from TypeScript.
7. Add targeted server tests and web tests for the new route's error shape and UI state. Route repo-wide command selection to `repo-development`.

## Evidence notes

Evidence came from `app/desktop/desktop_server.py`, `app/desktop/desktop.py`, `app/desktop/studio_server/*.py`, `app/desktop/studio_server/chat/`, `app/desktop/studio_server/jobs/`, `app/desktop/studio_server/webhost.py`, and desktop/studio server tests. Verified evidence covered `kiln-studio-desktop` 1.0.4 and a desktop `make_app` route table with 83 registered routes.
