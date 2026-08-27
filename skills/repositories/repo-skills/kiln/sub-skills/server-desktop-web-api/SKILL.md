---
name: server-desktop-web-api
description: "Run, inspect, and extend Kiln's REST server, MCP server, desktop
  studio server, Git sync, jobs, chat, OpenAPI schema bridge, and Svelte web
  UI."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Server, desktop, web API

Use this sub-skill when the task is about Kiln's FastAPI REST server, MCP server entrypoint, desktop studio server extensions, API route registration, Git sync middleware, background jobs and SSE streams, chat/agent endpoints, OpenAPI schema generation, or the Svelte web UI that consumes the generated API client.

Route core `.kiln` datamodel creation, persistence, CLI project packaging, and object signatures to `project-datamodel`. Route provider/model semantics, `adapter_for_task`, run-config execution behavior, tool IDs, and MCP task execution internals to `task-execution-providers-tools`. Route documents, extraction, vector stores, LanceDB, RAG indexing, and search semantics to `rag-documents-data`. Route evals, synthetic data generation, prompt optimization, fine-tuning, and repair workflows to `evals-optimization-finetuning`. Route repo-wide check policy, UI visual design standards, and general Svelte testing style to `repo-development`.

## Load these references

1. Read [rest-and-mcp-server.md](references/rest-and-mcp-server.md) for `kiln_server.make_app`, the `kiln_server` CLI, the `kiln_mcp` CLI, `connect_*_api` extension patterns, agent-policy metadata, core REST route surfaces, and MCP startup constraints.
2. Read [desktop-studio-server.md](references/desktop-studio-server.md) for `app.desktop.desktop_server.make_app`, desktop lifespan behavior, studio-only API registration, webhost catch-all ordering, CORS, and extension checklists.
3. Read [git-sync-jobs-chat.md](references/git-sync-jobs-chat.md) before changing Git sync, job registry/SSE behavior, chat streaming, Copilot proxying, agent overview, or endpoint lock annotations.
4. Read [openapi-and-web-ui.md](references/openapi-and-web-ui.md) before adding/changing routes used by the Svelte UI, regenerating `api_schema.d.ts`, editing stores/components/routes, or writing web tests.
5. Read [troubleshooting.md](references/troubleshooting.md) when imports, route registration, schema drift, CORS, Starlette/FastAPI versions, MCP imports, RAG optional imports, jobs/SSE, chat/Copilot, Git sync, or optional paid/provider services fail.

## Safe bundled helpers

Use [inspect_kiln_server.py](scripts/inspect_kiln_server.py) to import a Kiln FastAPI app and report route/tag coverage without starting uvicorn:

```bash
python scripts/inspect_kiln_server.py --app desktop --repo-root "$KILN_REPO_ROOT" --summary
python scripts/inspect_kiln_server.py --app server --list-routes
```

Use [check_openapi_schema.sh](scripts/check_openapi_schema.sh) from a Kiln checkout to run the OpenAPI schema freshness check through the bundled wrapper:

```bash
bash scripts/check_openapi_schema.sh --check
bash scripts/check_openapi_schema.sh --generate
```

The helpers are read-only by default. `--generate` intentionally updates the checkout's generated TypeScript schema.

## Operating rules

- Treat `kiln_server.make_app()` as the core REST surface and `app.desktop.desktop_server.make_app()` as the studio app that layers desktop APIs, Git sync middleware, jobs, chat, and the webhost on top.
- Keep `connect_webhost(app)` last in the desktop app; it mounts a root catch-all for the built web UI.
- Preserve CORS as the outermost middleware. Add caller middleware through `kiln_server.make_app(extra_middleware=[...])` when it must remain inner to CORS.
- Give every `/api/...` route a tag from `tags_metadata`, path/query parameter descriptions, and explicit `openapi_extra` agent policy metadata where relevant.
- Mark streaming or long-running endpoints that must bypass Git sync write-lock buffering with `@no_write_lock`; mark mutating `GET` endpoints with `@write_lock`.
- Use `CancellableStreamingResponse` for SSE routes that must tear down observers cleanly without cancelling background work.
- Regenerate/check the web OpenAPI client after changing Pydantic models, route paths, response models, path/query params, or tags used by the UI.
- Do not call optional paid providers, Ollama, cloud APIs, Copilot, remote MCP servers, or Git remotes while performing safe inspection unless the user explicitly asks and credentials/services are available.

## Evidence notes

This sub-skill is distilled from repo-relative evidence in `libs/server/README.md`, `libs/server/kiln_server/server.py`, `libs/server/kiln_server/mcp/README.md`, `libs/server/kiln_server/mcp/mcp.py`, `app/desktop/desktop_server.py`, `app/desktop/studio_server/`, `app/desktop/git_sync/`, `app/web_ui/package.json`, `app/web_ui/src/lib/api_client.ts`, `app/web_ui/src/lib/openapi_schema.sh`, web routes/stores/components/tests, and server/webhost/Git sync/jobs/chat tests. Verified package evidence covered `kiln-ai`, `kiln-server`, and `kiln-studio-desktop` 1.0.4, the CLI commands `kiln_ai`, `kiln_server`, and `kiln_mcp`, and a desktop `make_app` route table with 83 registered routes.
