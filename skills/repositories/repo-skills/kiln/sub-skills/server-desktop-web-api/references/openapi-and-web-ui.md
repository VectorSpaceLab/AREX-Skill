# OpenAPI and Svelte web UI

This reference covers Kiln's OpenAPI schema bridge and the Svelte web UI surfaces that consume the generated TypeScript client. Route visual design details, broad check policy, and general frontend style/testing conventions to `repo-development`.

## API client bridge

`app/web_ui/src/lib/api_client.ts` defines the shared web client:

```ts
import createClient from "openapi-fetch"
import type { paths } from "./api_schema"

const api_port = import.meta.env.VITE_API_PORT || "8757"
export const base_url = `http://localhost:${api_port}`
export const client = createClient<paths>({ baseUrl: base_url })
```

Implications:

- Route paths must match OpenAPI paths exactly, including `{project_id}` and `{task_id}` names.
- TypeScript callers should use `client.GET`, `client.POST`, `client.PATCH`, `client.DELETE`, etc., with `params.path`, `params.query`, and `body` objects matching generated types.
- The default API port is `8757`; Vite/dev tests may override `VITE_API_PORT`.
- If TypeScript cannot see a new endpoint or schema field, regenerate `api_schema.d.ts` before debugging the component.

## Schema generation and checking

The schema scripts live under `app/web_ui/src/lib/` in a Kiln checkout.

- `openapi_schema.sh` creates a temporary JSON OpenAPI schema.
- If `KILN_PORT` is set and a server responds at `/openapi.json`, it fetches that live schema.
- Otherwise it runs Python directly with `KILN_SKIP_REMOTE_MODEL_LIST=true` and imports `app.desktop.desktop_server.make_app().openapi()`.
- `generate_schema.sh` converts the schema to `api_schema.d.ts` with `npx openapi-typescript`.
- `check_schema.sh` generates a temporary TypeScript schema and diffs it against the committed `api_schema.d.ts`.

Commands from `app/web_ui`:

```bash
src/lib/check_schema.sh
src/lib/generate_schema.sh
```

Commands from repo root:

```bash
app/web_ui/src/lib/check_schema.sh
app/web_ui/src/lib/generate_schema.sh
```

Bundled helper from any Kiln checkout:

```bash
bash scripts/check_openapi_schema.sh --check
bash scripts/check_openapi_schema.sh --generate
```

Use `--check` for verification and `--generate` only when you intend to update generated TypeScript.

## Server-to-web change flow

When changing a route or model used by the UI:

1. Update the FastAPI route/Pydantic model.
2. Confirm every path/query parameter has a description. Tests inspect OpenAPI for missing descriptions.
3. Confirm every `/api/...` route has a documented tag.
4. Check route import does not call optional paid/cloud/Ollama/Copilot services during schema generation.
5. Run schema generation from a Kiln checkout.
6. Update web code to use generated `paths` and `components` types instead of duplicating backend shapes.
7. Add or update Vitest component/store tests for UI state and API wrapper behavior.
8. Run the targeted web check/test commands selected by `repo-development` guidance.

If schema generation fails while importing `make_app`, read [troubleshooting.md](troubleshooting.md) for dependency/version gotchas.

## Common web API wrapper pattern

The web stores and API helpers usually wrap `openapi-fetch` in a small function that throws on typed `error` and returns typed `data`:

```ts
export async function get_job(id: string): Promise<JobRecord> {
  const { data, error } = await client.GET("/api/jobs/{id}", {
    params: { path: { id } },
  })
  if (error) {
    throw error
  }
  return data
}
```

Prefer this pattern for reusable store APIs because components can stay focused on state/rendering. Keep endpoint-specific error interpretation close to the store/API helper when multiple components share it.

## Svelte source map

High-value web directories for this sub-skill:

| Area | Repo-relative source paths | Use for |
| --- | --- | --- |
| Shared API client | `app/web_ui/src/lib/api_client.ts`, `app/web_ui/src/lib/api_schema.d.ts` | OpenAPI client and generated types. |
| Global stores | `app/web_ui/src/lib/stores.ts`, `app/web_ui/src/lib/stores/` | Current project/task UI state, jobs, tools, skills, evals, run configs, prompts, chat UI state. |
| Jobs UI | `app/web_ui/src/lib/stores/jobs_api.ts`, `app/web_ui/src/lib/stores/jobs_store.ts`, `app/web_ui/src/lib/components/jobs_table.svelte`, `app/web_ui/src/lib/components/jobs_dialog.svelte`, `app/web_ui/src/routes/(app)/jobs/+page.svelte` | Job REST wrappers, EventSource state, tables/dialogs/pages. |
| Chat UI | `app/web_ui/src/lib/chat/`, `app/web_ui/src/routes/(app)/assistant/`, `app/web_ui/src/routes/(app)/chat_bar.svelte` | Streaming chat, session storage, assistant route, tool approval UI. |
| Git sync UI | `app/web_ui/src/lib/git_sync/`, `app/web_ui/src/lib/components/import/` | Git import wizard, OAuth flow, status, API wrappers. |
| Tools/run config UI | `app/web_ui/src/lib/stores/tools_store.ts`, `app/web_ui/src/lib/ui/run_config_component/`, `app/web_ui/src/routes/(app)/tools/` | MCP/tool selectors, run-config fields, tools pages. |
| Skills UI | `app/web_ui/src/lib/stores/skills_store.ts`, `app/web_ui/src/routes/(app)/skills/` | Project skill listing/forms/display. |
| Settings/providers | `app/web_ui/src/routes/(app)/settings/`, `app/web_ui/src/routes/(app)/models/`, `app/web_ui/src/lib/ui/kiln_copilot/` | Settings, provider/model/Copilot connection surfaces. |

## Jobs EventSource pattern

`jobs_store.ts` is the canonical EventSource pattern:

- Build URL from `base_url` and optional `project_id` filter.
- Listen for named `snapshot`, `job`, and `deleted` events.
- Treat stream open/close as pure observation; never mutate jobs from the SSE lifecycle.
- Reconnect after errors with a delay and use the fresh `snapshot` to resync; no `Last-Event-ID` is required.
- Track `synced` and connection state separately so the UI can distinguish loading from retrying.

When adding a new SSE stream, copy this shape: explicit event names, JSON parse isolation, active-source race checks, teardown on unsubscribe, and tests for reconnect/project-switch behavior.

## Chat UI pattern

The assistant route and chat library consume SSE events from `/api/chat` and `/api/chat/execute-tools`:

- The server proxies upstream AI SDK events, forwards `data:` lines, and adds Kiln-specific tool execution events.
- Tool calls that require user approval are surfaced as a pending event; the UI posts user decisions to continue the stream.
- The UI tracks chat sessions and local display state separately from the server trace/session payload.

Do not add chat UI code that silently executes approval-required tools. Preserve the explicit approval UI path.

## Testing pointers

Use targeted tests while iterating:

```bash
cd app/web_ui
npm run test_run -- --run src/lib/stores/jobs_store.test.ts
npm run test_run -- --run src/lib/git_sync/api.test.ts
npm run test_run -- --run src/lib/chat/streaming_chat.test.ts
npm run check
```

Before wrapping a web-facing change, route the exact command set and style/design review expectations to `repo-development`. Typical checks are `npm run lint`, `npm run format_check`, `npm run check`, `npm run test_run`, and `npm run build` from `app/web_ui`, plus the OpenAPI schema check.

## Evidence notes

Evidence came from `app/web_ui/package.json`, `app/web_ui/src/lib/api_client.ts`, `app/web_ui/src/lib/openapi_schema.sh`, `app/web_ui/src/lib/check_schema.sh`, `app/web_ui/src/lib/generate_schema.sh`, web stores/components/routes/tests, and server tests that assert OpenAPI tag/description/schema constraints.
