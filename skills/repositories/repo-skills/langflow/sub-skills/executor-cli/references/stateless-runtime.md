# Stateless Runtime Semantics

LFX is the lightweight Langflow Executor. It runs or serves flow definitions with fewer dependencies than the full Langflow application, but it deliberately does not provide the full Langflow database-backed runtime.

## Mental Model

Use this split when explaining behavior:

| Surface | Backing state | Best fit | Not best fit |
| --- | --- | --- | --- |
| `lfx run` | One process, one execution, no persistent app DB. | Offline smoke runs, CLI automation, serverless one-shot execution. | Saving flows, managing users, durable chat/message history. |
| `lfx serve` without `--flow-dir` | Per-worker in-memory flow registry. | Lightweight local/API execution, one worker, temporary uploads. | Multi-worker shared uploads, durable flow store, full Langflow app APIs. |
| `lfx serve --flow-dir DIR` | Flow JSON persisted to a filesystem store, graph cache per worker. | Shared flow registry across workers or pods that share `DIR`. | Durable database semantics, Python script graph persistence, user/message storage. |
| Full `langflow run` server | Database and services configured by Langflow. | Visual builder, saved flows, users, API keys, message history, auth/authz, projects. | Minimal executor-only deployment. |

## `NoopSession` and Database Caveat

LFX uses a `NoopSession` implementation for database-session-shaped operations. Its methods exist so components can call session-like APIs, but they do not persist data:

- `add`, `commit`, `rollback`, `refresh`, `delete`, and `close` are no-ops.
- `execute` returns `None`.
- `query` returns an empty list.
- `get` returns `None`.
- `exec` returns an object whose `first()` and `one_or_none()` are `None`, `all()` is empty, and iteration yields nothing.
- `no_autoflush` and context-manager methods are no-op compatibility hooks.

Result: operations that depend on Langflow's application database, such as saving flows to the app DB, storing users, persisting messages, or reading DB-backed variables, do not work the same way under `lfx run` or `lfx serve`.

## Memory and Session Behavior

`--session-id` and request `session_id` still matter, but they are not enough to create durable persistence by themselves.

- `lfx run` auto-generates a session id when none is provided so graph execution and memory prechecks do not fail.
- `lfx run --session-id ID` propagates the session id to Memory/MessageHistory vertices when the flow JSON did not hardcode one.
- Empty or whitespace-only session ids are rejected because they usually indicate a shell/env-var mistake.
- `lfx serve` accepts `session_id` in `/run` and `/stream` request bodies and applies the same default/propagation logic to a deep copy of the graph.
- Under LFX's no-op database session, memory/message-history components that rely on the Langflow DB cannot retrieve prior turns across separate CLI runs or server requests.
- If `lfx` is used as a Python library inside a full Langflow server where real services are registered, memory operations may route to the full Langflow implementation. Do not assume that behavior for the `lfx run` or `lfx serve` command-line paths.

When a user asks why memory is empty despite passing the same `session_id`, answer: the executor can stamp the session id into the graph, but the lightweight CLI path has no durable Langflow message database; stateful memory components need a real backing service or a component-specific external store.

## Flow Registry Persistence

### `lfx run`

`lfx run` loads a JSON flow, inline JSON, stdin JSON, or a trusted Python graph script for a single execution. It does not register or save the flow anywhere.

### `lfx serve` Default Store

Without `--flow-dir`, `lfx serve` uses an in-memory flow registry:

- Startup files are loaded into each process.
- Uploaded flows are visible only inside the worker process that handled the upload.
- Deleting a flow removes it from that worker only.
- Restarting the server loses uploaded flows.
- With multiple workers and no `--flow-dir`, LFX warns that each worker has an isolated in-memory registry.

### Filesystem Store with `--flow-dir`

With `--flow-dir`, LFX writes flow JSON as `{flow_id}.json` and workers use the directory as a shared flow store:

- Startup JSON flows are written to the store.
- Uploads through `POST /flows/upload/` are written atomically to the store.
- Workers warm their own in-memory graph cache from the store.
- Deleting a flow removes the JSON file; other workers evict stale cached copies on their next request for that flow.
- Existing files whose filename stem differs from the JSON `id` may be served by both the stem alias and canonical UUID until normalized by replacement/deletion logic.
- Corrupted or unreadable store files are logged and skipped so one bad file does not prevent other flows from serving.

`--flow-dir` stores flow definitions only. It does not store users, API keys, request logs, chat messages, variables, projects, or full Langflow database state.

## Multi-worker Rules

Use this decision table:

| Need | Command pattern | Reason |
| --- | --- | --- |
| One local worker | `lfx serve flows/my-flow.json` | Simpler, all flows in memory. |
| Several workers sharing JSON flows | `lfx serve flows/ --workers 4 --flow-dir ./lfx-flow-store` | Startup JSON and uploads are visible to all workers through the filesystem store. |
| Several workers with `.py` graph scripts | Avoid `--flow-dir`; prefer exporting to JSON or use one worker. | Python graph objects cannot be serialized into the flow store. |
| Cross-pod shared flows | `--flow-dir` on a shared volume | Works for JSON flows, but network filesystem reads can add latency. |
| Durable app data | Use full `langflow run` with configured DB. | LFX flow store is not a database. |

## API Key Semantics for `lfx serve`

`lfx serve` requires a token in the environment before startup:

- `LANGFLOW_API_KEY` is preferred.
- `LFX_API_KEY` is accepted as fallback.
- The same value must be supplied to requests as `x-api-key` header or `?x-api-key=` query parameter.
- Missing request key returns `401 API key required`.
- Wrong request key returns `401 Invalid API key`.
- If the server environment no longer has an expected key, request verification can return a `500` with the key-configuration error.

This API key protects the lightweight executor endpoints. It is not automatically stored in a Langflow database and does not create a user or project.

## Variable and Credential Resolution

### `lfx run`

During execution, LFX resolves DB-style `load_from_db` variables with fallback to environment variables when the settings service allows it. Since LFX has no persistent variable database, provider credentials are normally supplied through environment variables.

Use `--check-variables` before execution to catch missing global variables; use `--no-check-variables` only when intentionally deferring variable resolution or when validation is too strict for a known flow.

### `lfx serve`

Served flows use a copy of the graph per request. The request may include:

```json
{
  "input_value": "Hello",
  "global_vars": {
    "LANGFLOW_REQUEST_VARIABLES": "{\"OPENAI_API_KEY\":\"replace-with-request-key\"}",
    "x-langflow-global-var-custom-token": "replace-with-request-token"
  }
}
```

Resolution order for variables in the minimal variable service:

1. In-memory variable-service values set during this process.
2. Request-scoped exact names from `global_vars` or parsed `LANGFLOW_REQUEST_VARIABLES`.
3. Request-scoped `x-langflow-global-var-*` aliases.
4. Process environment exact names, unless no-env fallback is active.
5. Process environment aliases, unless no-env fallback is active.

`LANGFLOW_REQUEST_VARIABLES` values must be a JSON object when supplied as a string. Dict/list values are serialized as JSON strings; `null` values are dropped.

### `--no-env-fallback`

`lfx serve --no-env-fallback` stamps each graph so request execution does not read process-wide environment variables for credentials. Variables not supplied via request `global_vars` resolve to `None`.

Use this for multi-tenant or externally exposed executor deployments. It prevents accidental use of ambient process credentials, but custom components that explicitly write to or read from `os.environ` are outside this guarantee.

## Flow Upload and Request Shape

`POST /flows/upload/` accepts a full Langflow export JSON body with at least:

```json
{
  "name": "My Flow",
  "description": "Optional",
  "id": "optional-uuid",
  "data": {"nodes": [], "edges": []}
}
```

- If `id` is omitted, the server generates a UUID.
- If `id` is present, it must be a valid UUID.
- Uploading a duplicate ID without `replace=true` returns `409`.
- Invalid JSON shape or graph preparation failure returns `422`.

`POST /flows/{flow_id}/run` request body:

```json
{
  "input_value": "Hello world",
  "session_id": "optional-session-id",
  "global_vars": {"OPENAI_API_KEY": "replace-with-request-key"}
}
```

`POST /flows/{flow_id}/stream` adds `input_type`, `output_type`, `output_component`, and `tweaks` fields. The stream route accepts `tweaks`, but the current simplified server-side generator primarily executes the graph with `input_value` and `session_id`; if a task needs full Langflow API run semantics, route to backend/API guidance.

## Component Category Filters

LFX can restrict component categories at component-index load time:

| Environment variable | Effect |
| --- | --- |
| `LANGFLOW_COMPONENT_CATEGORY_ALLOWLIST` | Comma-separated category names to include. Empty means include all. |
| `LANGFLOW_COMPONENT_CATEGORY_BLOCKLIST` | Comma-separated category names to exclude after allowlist. Empty means exclude none. |

The virtual category `core` expands to common built-in categories such as inputs/outputs, models, agents, prompts, data, logic, tools, vector stores, document loaders, and related core groups. If a flow fails with unknown components under LFX, check these filters before assuming the flow JSON is bad.

## Upgrade Compatibility Semantics

`lfx upgrade`, `lfx run --upgrade-flow`, and `lfx serve --upgrade-flow` use the bundled component registry as the compatibility source.

- `lfx upgrade FLOW.json`: prints status and exits non-zero for blocked/breaking components.
- `lfx upgrade FLOW.json --write`: writes safe upgrades to the file.
- `--upgrade-flow check`: refuses to run/serve when any component is not clean.
- `--upgrade-flow safe`: applies safe upgrades in memory before run/serve and aborts on breaking/blocked components.

If the bundled registry is missing or empty, compatibility checks fail loudly and suggest reinstalling `lfx`; do not treat every blocked component as a flow-authoring problem until the registry is confirmed healthy.

## What to Say in the Two Required Hard Cases

### Serve Two Flow Files with `--flow-dir` and `--no-env-fallback`

Use:

```bash
export LANGFLOW_API_KEY="replace-with-local-token"
lfx serve flows/a.json flows/b.json \
  --workers 2 \
  --flow-dir ./lfx-flow-store \
  --no-env-fallback
```

Then send per-request credentials:

```bash
curl -X POST "http://localhost:8000/flows/$FLOW_ID/run" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $LANGFLOW_API_KEY" \
  -d '{"input_value":"Hello","global_vars":{"OPENAI_API_KEY":"replace-with-request-key"}}'
```

API-key behavior is preserved because the server authentication token still comes from `LANGFLOW_API_KEY`/`LFX_API_KEY`; `--no-env-fallback` affects component credential resolution inside flow execution, not the endpoint authentication check.

### Explain Why Memory/State Is Not Persisted Under `NoopSession`

Say: `lfx` provides session ids and a database-session-shaped adapter so components can execute, but the CLI executor does not open or write a Langflow database. `NoopSession` commits nothing and queries return empty/none. Therefore Memory/MessageHistory components that expect Langflow DB rows can see the stamped `session_id` but cannot retrieve prior messages across separate LFX executions. Use full Langflow server/database or a component-specific external memory store for durable state.
