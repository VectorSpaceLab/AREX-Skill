# Server API and protocol surface

This reference covers the operational HTTP/SSE surface served by `gptme-server` and the small Python `GptmeApiClient` helper used by server-side integrations.

## Install and entry points

Typical end-user server install:

```bash
pipx install 'gptme[server]'
```

The package exposes these server-related console scripts:

- `gptme-server` -> `gptme.server.cli:main`.
- `gptme-tui` -> `gptme.tui.main:main`.
- `gptme-acp` -> `gptme.acp.__main__:main`.

`gptme-server` uses a default command group: running `gptme-server` with no subcommand starts `serve`.

### Safe help and import checks

These checks are read-only and are appropriate before deeper troubleshooting:

```bash
gptme-server --help
gptme-server serve --help
gptme-server token --help
gptme-server openapi --help
python -c "from gptme.server.app import create_app; app=create_app(); print(len(app.url_map._rules))"
```

Expected signals:

- `gptme-server --help` lists `serve`, `token`, and `openapi`.
- `gptme-server serve --help` lists `--host`, `--port`, `--cors-origin`, `--allowed-hosts`, `--webui-dir`, `--default-profile`, `--exit-on-parent-death`, and `--watch-pid`.
- The `create_app()` smoke prints a positive route count if server extras import successfully.

Do not run full server tests, browser E2E, Docker, or model calls unless the user is maintaining a checkout and explicitly authorizes those heavier checks.

## Server factory and UI selection

Verified factory signature:

```python
create_app(cors_origin=None, host='127.0.0.1', webui_dir=None, default_profile=None, allowed_hosts=None)
```

The server chooses the static UI directory in this order:

1. explicit `webui_dir` argument or `--webui-dir`
2. `GPTME_WEBUI_DIR`
3. bundled modern Web UI at package path `gptme/server/webui-dist` when populated
4. embedded legacy fallback at package path `gptme/server/static`

A configured custom UI directory must exist; a typo should fail at startup instead of silently serving 404s. For custom React/Vite builds, `/`, `/chat`, `/computer`, and unknown SPA paths serve `index.html` unless the path is an existing asset or an API path.

## Serve options that matter

| Option | Purpose | Notes |
| --- | --- | --- |
| `--host` | Bind address | Defaults to `127.0.0.1`; `0.0.0.0` exposes the server beyond loopback. |
| `--port` | Listen port | Defaults to `5700`. |
| `--model` | Default model | Request config can still override per conversation/step. |
| `--tools` | Tool allowlist | Comma-separated names; `none` disables all tools and cannot be combined with other names. |
| `--cors-origin` | Browser CORS allow-list | Exact origin or comma-separated trusted origins; `*` disables credential/PNA opt-in behavior. |
| `--allowed-hosts` | Extra Host-header allow-list | Relevant when bearer auth is explicitly disabled. Also available through `GPTME_SERVER_ALLOWED_HOSTS`. |
| `--webui-dir` | Custom Web UI build directory | Overrides the bundled UI. |
| `--default-profile` | Default profile for new conversations | Useful for specialized deployments such as computer-use backends. |
| `--exit-on-parent-death` | Sidecar cleanup | Exits when the parent process dies. |
| `--watch-pid` | Sidecar cleanup with wrapper PID | Watches a specific PID instead of the immediate parent. |
| `--debug`, `--verbose` | Development diagnostics | Avoid debug mode on public deployments. |

## Authentication model

Bearer authentication is required for capability-bearing routes on every bind address unless `GPTME_DISABLE_AUTH` is explicitly set. Loopback is not treated as identity; another local process still needs a token.

Token behavior:

- If `GPTME_SERVER_TOKEN` is set, the server uses that stable token.
- If it is unset, the server generates a random token at startup and prints it to logs.
- A generated token is valid only for that process lifetime. Persistent deployments should set a stable token or every restart invalidates existing Web UI/client settings.
- `gptme-server token` prints the current token for the current process environment, or reports that auth is disabled.

Auth mechanisms checked by protected endpoints, in order:

1. `Authorization: Bearer <token>` header.
2. HttpOnly cookie named by the server auth implementation; the Web UI obtains it with `POST /api/v2/auth/cookie`.
3. `?token=<token>` query parameter for legacy/SSE fallback. Avoid it when cookie or header auth is possible because URLs can be logged.

Public unauthenticated routes in the default model:

- `GET /api/v2`
- `GET /api/v2/version`
- `GET /api/v2/config`
- `GET /api/docs/`
- `GET /api/docs/openapi.json`
- `GET /api/v0/metrics`
- static UI routes such as `/` and `/chat`

Security boundary: any authorized API client can cause the agent to execute arbitrary shell/file operations through tools. The server is single-user; put multi-user boundaries in the OS, network, ingress, or deployment layer.

## CORS, Host validation, and Local Network Access

### CORS origin

`--cors-origin` only controls which browser origins receive CORS response headers for `/api/*`. Use the exact page origin, for example:

```bash
gptme-server --cors-origin 'http://localhost:5701'
gptme-server --cors-origin 'https://chat.gptme.org'
gptme-server --cors-origin 'tauri://localhost,http://tauri.localhost,https://tauri.localhost'
```

Comma-separated origins are trimmed. A non-matching origin may still get a Flask 200 at the HTTP layer, but the browser will hide the response because the allow-origin header is absent.

Wildcard CORS (`*`) is not equivalent to trusted-origin CORS: browsers reject credentials with wildcard origins, and the server deliberately does not opt wildcard origins into Private Network Access.

### Chrome Local Network Access

When a public/hosted HTTPS page reaches `localhost`, `127.0.0.1`, or a private-address server, modern Chromium may block the request before normal CORS is evaluated unless the user grants Local Network Access permission. The server adds `Access-Control-Allow-Private-Network: true` only for named non-wildcard CORS origins. The user still has to click the browser permission prompt.

For hosted UI -> local server support, all three must be correct:

1. exact `--cors-origin` for the UI origin
2. browser Local Network Access permission when prompted
3. valid bearer token/cookie/query fallback for protected routes

### Host-header validation

Host validation is a DNS-rebinding defense-in-depth layer used when bearer auth is explicitly disabled. Defaults always allow loopback hostnames. If auth is disabled and a reverse proxy uses a custom host, add it with:

```bash
gptme-server serve --allowed-hosts gptme.local
```

Keep bearer auth enabled unless an authenticated external ingress owns all access.

## Workspace create/update security semantics

Conversation creation and update intentionally differ:

- `PUT /api/v2/conversations/<id>` may accept an explicit workspace path from an authorized client. The assumption is that an authorized client could already run shell commands; creation-time workspace containment is not a security boundary.
- `PATCH /api/v2/conversations/<id>/config` accepts the already-persisted workspace round-trip, but rejects retargeting an existing conversation outside its log directory. This avoids confused-deputy workspace redirects mid-conversation.

Deleting and recreating a conversation is the intended way to switch arbitrary workspace roots after creation. Deletion is destructive; export or back up logs first when needed.

## API route families

### Static/UI/meta

- `GET /` — served Web UI `index.html`.
- `GET /chat` — SPA entry for chat routes.
- `GET /computer` — legacy computer page or SPA entry for custom UI builds.
- `GET /favicon.png` — package media logo.
- `GET /api/v2` — API root with package version, `api_version`, `contract_revision`, capability summary, and provider-configured flag.
- `GET /api/v2/version` — compact API version/contract check with `X-API-Version` header.
- `GET /api/v2/config` — agent metadata from project config.
- `GET /api/docs/` and `GET /api/docs/openapi.json` — Swagger UI and OpenAPI JSON.

### Conversations and messages

- `GET /api/v2/conversations` — list/search/paginate conversations. `detail=true` performs slower full cost/token scans.
- `GET /api/v2/conversations/<id>` — fetch conversation log, branches, workspace, agent info, pagination metadata, and latest session state.
- `PUT /api/v2/conversations/<id>` — create a conversation and server session.
- `POST /api/v2/conversations/<id>` — append a message; accepts branch and optional tool allowlist.
- `PATCH /api/v2/conversations/<id>/messages/<index>` — edit/truncate a message.
- `DELETE /api/v2/conversations/<id>/messages/<index>` — delete a message.
- `POST /api/v2/conversations/<id>/fork` — fork from a message index.
- `GET /api/v2/conversations/<id>/config` — read chat config.
- `PATCH /api/v2/conversations/<id>/config` — update chat config with workspace retargeting guardrails.
- `DELETE /api/v2/conversations/<id>` — delete a conversation and remove sessions.

### Real-time step control

- `GET /api/v2/conversations/<id>/events` — SSE event stream; creates a session when `session_id` is absent.
- `POST /api/v2/conversations/<id>/step` — start/continue generation. Important request fields include `session_id`, optional `model`, `stream`, `auto_confirm`, `branch`, `use_acp`, sampling overrides, and optional `message`.
- `POST /api/v2/conversations/<id>/tool/confirm` — confirm, edit, skip, or auto-confirm a pending tool.
- `POST /api/v2/conversations/<id>/rerun` — rerun tools from the last assistant message.
- `POST /api/v2/conversations/<id>/elicit/respond` — answer an elicitation request.
- `POST /api/v2/conversations/<id>/interrupt` — interrupt active generation or tool execution.
- `POST /api/v2/conversations/<id>/transcript` — append voice transcript turns with idempotency metadata.

### Workspace and files

- `GET /api/v2/conversations/<id>/workspace[/<subpath>]` — browse workspace or return file metadata.
- `POST /api/v2/conversations/<id>/workspace/upload` — upload attachments.
- `GET /api/v2/conversations/<id>/files/<path>` — serve conversation file/attachment.
- `GET /api/v2/conversations/<id>/workspace/<path>/preview` — preview text/data files; binary files return metadata.
- `GET /api/v2/conversations/<id>/workspace/<path>/download` — download file bytes.

### Admin, user, and integration surfaces

- `GET /api/v2/sessions`, `DELETE /api/v2/sessions/<id>` — active session admin.
- `GET /api/v2/server/health` — lightweight health summary: session count, generating count, idle count, color, and slot list.
- `GET /api/v2/commands` — slash command catalog.
- `GET /api/v2/models` and `GET /api/v2/providers/health` — model/provider discovery and health.
- `GET /api/v2/tools`, `QUERY /api/v2/tools` — tool metadata and safe body-capable filtering.
- `GET /api/v2/skills` — discoverable skills with reputation metadata.
- `GET /api/v2/conversations/<id>/artifacts` and `GET /api/v2/conversations/<id>/artifacts/<artifact_id>` — artifact descriptors.
- `GET /api/v2/conversations/<id>/panels` — panel registry from `metadata.panel_hints`.
- `GET /api/v2/tasks` plus related task create/update/archive routes.
- `GET /api/v2/external-sessions`, `GET /api/v2/external-sessions/<id>`, `POST /api/v2/external-sessions/<id>/steer` — external session catalog, normalized transcript, and steering.
- `GET /api/v2/computer/status`, `GET /api/v2/computer/screenshot` — computer-use status/screenshot helpers.
- `POST /api/v2/audio/transcriptions` and `POST /api/v2/audio/speech` — speech helpers through OpenRouter-backed routes.
- `GET /api/v2/user` and `/api/v2/user/*` — user identity, avatar, config file, API key/default-model/favorites/settings helpers.
- `PUT /api/v2/agents`, `GET /api/v2/agents`, `GET /api/v2/agents/avatar` — agent creation/list/avatar helpers.
- `GET /.well-known/agent-card.json`, `GET /.well-known/agent.json`, and the A2A JSON-RPC path — agent-to-agent integration surfaces.

## SSE event contract

The event stream sends JSON as `data: {...}\n\n` records with MIME type `text/event-stream`, `Cache-Control: no-cache`, and `X-Accel-Buffering: no` for proxy friendliness.

Important events:

| Event | Key fields | Operational meaning |
| --- | --- | --- |
| `connected` | `session_id`, `generating`, `last_error`, `pending_tools` | Initial handshake and reconnect state. |
| `ping` | none | Keepalive. |
| `generation_started` | none | UI should create/mark the assistant streaming placeholder. |
| `generation_progress` | `token` | Batched token chunk. |
| `generation_complete` | `message` | Final assistant message including `timestamp` and `metadata`. |
| `message_added` | `message` | A persisted message was appended; used for tool outputs, hook messages, and non-stream additions. |
| `tool_pending` | `tool_id`, `tooluse`, `auto_confirm` | Tool confirmation state. |
| `tool_executing` | `tool_id` | Pending tool moved into execution. |
| `tool_output` | `tool_id`, `output` | Partial visible tool output. |
| `tool_complete` | `tool_id`, `duration_ms`, `success` | Execution completed; timing may later be persisted to message metadata. |
| `elicit_pending` | `elicit_id`, `elicit_type`, prompt/options/fields | Agent requested structured input. |
| `interrupted` | none | Active work was interrupted. |
| `error` | `error` | Server/generation/tool failure. |
| `config_changed` | `config`, `changed_fields` | Conversation config changed, including auto-naming. |
| `conversation_edited` | `index`, `truncated`, `log`, `branches` | Edit/delete mutation changed the log. |

Consistency rule: both `message_added` and `generation_complete` use `msg2dict(...)` to serialize `Message` objects. If REST and SSE disagree, inspect that serialization path first.

## Message dictionary and Web UI metadata

Message dictionary fields:

- required: `role`, `content`, `timestamp`
- optional: `files`, `hide`, `call_id`, `metadata`

Main Web UI display fields read from `metadata`:

- `model`
- `resolved_model`
- `cost`
- `usage.input_tokens`
- `usage.output_tokens`
- `usage.cache_read_tokens`
- `usage.cache_creation_tokens`
- `tool`

Additional backend surfaces also read metadata:

- `panel_hints` for the panels API/UI.
- `artifacts` for artifact descriptors.
- `timings` for backend/tool timing persistence.
- `voice_call` for voice transcript idempotency.

Use [../scripts/check_webui_message_metadata.py](../scripts/check_webui_message_metadata.py) when debugging badge, cost, token, panel, or SSE/REST mismatch reports.

## `GptmeApiClient`

Verified signature:

```python
GptmeApiClient(base_url='http://localhost:5000', auth_token=None)
```

The default base URL is older than the server's common local port. Pass the actual deployment URL, typically `http://127.0.0.1:5700`.

Methods:

- `create_session(conversation_id) -> str` — opens the events stream and returns the `session_id` from the initial `connected` event.
- `take_step(conversation_id, session_id, message=None, auto_confirm=True, stream=True) -> dict` — POSTs a step request.
- `stream_events(conversation_id, session_id)` — yields `ConversationEvent(type, data)` parsed from SSE `data:` lines.
- `interrupt(conversation_id, session_id) -> dict` — interrupts active work.
- `confirm_tool(conversation_id, session_id, tool_id, action='confirm', content=None, auto_continue=False) -> dict` — resolves a pending tool.
- `execute_conversation(conversation_id, prompt, auto_confirm=True) -> tuple[bool, str | None]` — convenience wrapper that creates a session, sends a prompt, and waits for `generation_complete` or `error`.

## Safe server probing

Use [../scripts/probe_gptme_server.py](../scripts/probe_gptme_server.py) for read-only server checks. Example:

```bash
python skills/disco/gptme/sub-skills/server-webui-and-protocols/scripts/probe_gptme_server.py --base-url http://127.0.0.1:5700 --token '<token>'
```

The probe checks the web root, API root, version endpoint, and server health. A `401` from health without a token means the server is alive but protected; it is not itself a routing failure.
