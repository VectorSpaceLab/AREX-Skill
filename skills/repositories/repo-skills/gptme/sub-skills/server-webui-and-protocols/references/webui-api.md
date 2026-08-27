# Web UI, frontend API, and rendering contracts

This reference covers the gptme Web UI deployment modes and the frontend/backend protocol details that matter when a server, browser, or message payload misbehaves.

## Deployment modes

The same Web UI codebase is used in several modes:

| Mode | Server relationship | Operational notes |
| --- | --- | --- |
| Bundled local UI | Same origin as `gptme-server` | Run `gptme-server` and open the server root, usually `http://localhost:5700`. No CORS needed. |
| Vite local development | Frontend at `http://localhost:5701`, backend at `http://localhost:5700` | Start backend with `--cors-origin 'http://localhost:5701'`. |
| Desktop app/sidecar | Desktop shell launches a local server sidecar | Include sidecar origin(s) in CORS when the webview is not same-origin; use parent-death watcher options. |
| Hosted open UI | Static hosted UI connects to a user-supplied server | Requires exact CORS origin, token, and possibly Local Network Access permission for local/private servers. |
| Custom remote | Browser UI connects to VM/workstation/server URL | Configure the server URL and token in Settings; check proxy buffering for SSE. |

The Web UI supports multiple configured servers. Server configs include a display name, base URL, optional auth token, and flags such as `useAuthToken`/preset status. Conversation summaries are tagged with server identity so the sidebar can merge conversations from several servers.

## Bundled UI vs custom/Vite UI

`gptme-server` serves static assets through the Flask app. Selection order:

1. explicit `--webui-dir`
2. `GPTME_WEBUI_DIR`
3. bundled modern build in package path `gptme/server/webui-dist` when populated
4. legacy static fallback in package path `gptme/server/static`

For same-origin bundled use:

```bash
gptme-server
# open http://localhost:5700
```

For frontend development:

```bash
# terminal 1, backend
gptme-server --cors-origin 'http://localhost:5701'

# terminal 2, frontend checkout
cd webui
npm i
npm run dev
```

Useful frontend commands from the package script map:

```bash
npm run build           # type-check then build
npm run lint            # ESLint plus TypeScript check
npm run typecheck       # TypeScript only
npm run typecheck:watch # watch mode
npm test                # Jest unit tests
npm run test:coverage   # coverage
npm run test:e2e        # Playwright E2E
npm run test:e2e:ui     # Playwright interactive UI
```

Maintainer-only note: these Node commands mutate/install dependencies and belong to a target checkout maintenance workflow. Do not run them for routine server operation unless the user is maintaining that checkout.

## Frontend connection behavior

The main frontend client is the `ApiClient` implementation. Operational behavior:

- It probes `GET /api/v2` first to validate reachability and inspect `api_version`/`contract_revision`.
- It classifies connection failures as `network`, `cors`, `timeout`, `http_error`, or `parse_error` for user-facing recovery hints.
- It includes `Authorization: Bearer <token>` on fetch requests when a token is configured.
- It tries to set an HttpOnly auth cookie with `POST /api/v2/auth/cookie` for same-origin SSE.
- It skips the cookie path for cross-origin EventSource requests because SameSite=Lax cookies are not sent cross-origin; it falls back to `?token=` for SSE when needed.
- It opens `EventSource(..., { withCredentials: true })`, reconnects with exponential backoff, and reuses `session_id` when available.
- It applies Local Network Access request hints only for loopback/private target URLs.

If a user says "the page loads but cannot connect to the server," inspect the connection-state reason before assuming the server process is down.

## REST/SSE data flow

The Web UI relies on the same message dictionary shape from both REST and SSE:

- REST `GET /api/v2/conversations/<id>` uses `LogManager.to_dict()` and `Message.to_dict()`.
- SSE `message_added` and `generation_complete` use `msg2dict(...)` in the server common API layer.
- `ApiClient.subscribeToEvents(...)` dispatches event callbacks by event type.
- `useConversation(...).onMessageComplete(...)` updates the last assistant placeholder with final `content`, `metadata`, and `timestamp` from `generation_complete`.
- `connected` event state restores `session_id`, `generating`, `last_error`, and pending tools on reconnect.

This makes metadata consistency critical. A bug can show up as:

- REST history shows model/cost but the streamed message loses the badge.
- The streamed message shows one timestamp/model while refresh shows another.
- Pending tool state survives on the server but the UI does not restore it after reconnect.

Use [../scripts/check_webui_message_metadata.py](../scripts/check_webui_message_metadata.py) to compare representative REST and SSE samples.

## Message metadata fields

Main display contract for `message.metadata`:

| Field | UI use |
| --- | --- |
| `model` | Requested/effective model label. |
| `resolved_model` | Actual routed provider/model label; displayed instead of `model` when present. |
| `cost` | Per-message cost badge/tooltip. |
| `usage.input_tokens` | Token/cost summary. |
| `usage.output_tokens` | Token/cost summary. |
| `usage.cache_read_tokens` | Cache token summary. |
| `usage.cache_creation_tokens` | Cache token summary. |
| `tool` | Tool-activity display for system/tool-result messages. |
| `panel_hints` | Panel registry surface for rich panels. |

Backend-only or secondary fields may still be preserved, for example `timings`, `voice_call`, `artifacts`, and prompt-generation details.

## Markdown rendering paths

The Web UI has two independent markdown rendering paths:

1. Chat streaming path: `ChatMessage.tsx` -> streaming markdown renderer.
2. Non-chat/preview path: `parseMarkdownContent()` -> `marked` renderer.

The gptme fence convention is unusual: a fence line with a language tag, such as ```` ```python ````, is always an opener, and a bare ```` ``` ```` is the closer. The helper `processNestedCodeBlocks()` widens outer fences before parsing so nested code blocks render correctly.

When changing markdown preprocessing, code block summaries, thinking-tag rendering, or code block icons, apply the change to both paths. If only one path changes, chat messages and previews drift.

## Step grouping model

The Web UI collapses intermediate tool-use steps with `buildStepRoles(...)`:

- A turn spans from one user message to the next user message.
- The final visible response is the last assistant message in that span that is not immediately followed by a recognized tool-result system message.
- Intermediate assistant/system tool-use messages become a collapsible step group.
- Group IDs use the absolute index of the first grouped step so expansion state remains stable when older messages are prepended.
- Step count is primarily the number of system tool-result messages, not the raw number of messages.

Implications:

- Hidden/system hook messages can affect grouping if they look like tool results.
- A missing or malformed system tool result can cause the assistant tool call to appear as a final response.
- Pagination must preserve absolute offsets when computing group IDs.

## `ChatInput` state and streaming interaction

Important state behaviors:

- `ChatInput` stays mounted while switching conversations, so `useState` initializers do not re-run automatically.
- Draft persistence uses local storage keys derived from the conversation id, commonly `gptme-draft-<conversationId>`.
- The input can queue a message while generation is busy and send it after the current step completes.
- Escape/interrupt flows call the server interrupt endpoint and then clear pending/executing state in the conversation store.
- Workspace and model badges can be stale if the conversation-switch sync path is bypassed.

When fixing input state bugs, test a conversation switch, a queued prompt, an interrupt, and a server reconnect before declaring the UI state fixed.

## Legend State gotcha

Some list rendering uses Legend State observables and `<For>`. React `useState` inside `<For>` callbacks is invisible to observable re-rendering; use an observable when the value must trigger item updates. This is a maintainer-only frontend implementation concern, but it explains many "state changed but UI did not update" reports.

## Browser connection patterns

### Same-origin bundled UI

Symptoms are usually token or server errors, not CORS. Check:

```bash
python skills/disco/gptme/sub-skills/server-webui-and-protocols/scripts/probe_gptme_server.py --base-url http://127.0.0.1:5700 --token '<token>'
```

### Vite frontend to local backend

Backend must allow `http://localhost:5701` exactly:

```bash
gptme-server --cors-origin 'http://localhost:5701'
```

If the frontend uses `127.0.0.1` while the CORS origin uses `localhost`, treat that as an origin mismatch.

### Hosted UI to local backend

Check three layers:

1. `--cors-origin` matches the hosted UI origin.
2. Browser Local Network Access permission is granted.
3. The configured server token matches the server process.

Opening the local server root directly in the browser can help trigger or diagnose the LNA/token path.

## Version-skew note

The frontend evidence includes helper code for conversation metadata sidecars under `/api/v2/conversations/<id>/metadata`, while the inspected backend route set did not expose a matching route. Treat that exact surface as version-skewed for this source snapshot unless a future target checkout adds the backend endpoint.
