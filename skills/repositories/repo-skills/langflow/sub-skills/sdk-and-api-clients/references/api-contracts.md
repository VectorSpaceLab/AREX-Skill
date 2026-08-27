# API Contracts

This reference summarizes Langflow REST and OpenAPI contracts relevant to client integration. It is self-contained for future agents writing API clients or validating examples.

## Base URL And Authentication

Default local server URL is `http://localhost:7860`. REST paths are rooted under `/api/v1` for current flow/project/run operations. The workflow OpenAPI also documents `/api/v2/workflows` endpoints.

Use these headers for JSON requests:

```text
Content-Type: application/json
accept: application/json
x-api-key: <api key when auth is enabled>
```

For flow run requests, `X-LANGFLOW-GLOBAL-VAR-{VARIABLE_NAME}` headers can pass temporary global variables to a run. Header-provided global variables are uppercased, apply only to that request, and take precedence over OS environment variables. If a flow references missing variables, it can fail unless the server is configured to fall back to environment variables.

## OpenAPI Specs

Evidence included the generated main API and workflow API OpenAPI specs. The inspected main spec reported title `Langflow`, version `1.10.0`, and 94 paths. The inspected workflow spec reported title `Langflow V2 Workflow API`, version `1.10.0`, and paths `/api/v2/workflows` and `/api/v2/workflows/stop`.

When validating API examples, use an available OpenAPI spec as the source of route existence and method names, then use SDK models/tests as the source for client-side helper behavior. OpenAPI versions can lag package patch versions; note the spec version separately from installed package versions.

## Flow Management Endpoints

Use `/api/v1/flows/` and `/api/v1/flows/{flow_id}` for CRUD.

| Capability | Method/path | Notes |
| --- | --- | --- |
| Create flow | `POST /api/v1/flows/` | Body resembles `FlowCreate`; include `name` and optional `data`, `endpoint_name`, tags, folder/project ID, icon, lock, and MCP settings. |
| Create batch | `POST /api/v1/flows/batch/` | Creates multiple flow objects. |
| List flows | `GET /api/v1/flows/` | Query parameters include pagination and filters; SDK exposes `folder_id`, `remove_example_flows`, `components_only`, `get_all`, `header_flows`, `page`, and `size`. |
| Read flow | `GET /api/v1/flows/{flow_id}` | Returns a flow object. |
| Update flow | `PATCH /api/v1/flows/{flow_id}` | Patch only sent fields. |
| Upsert flow | `PUT /api/v1/flows/{flow_id}` | Used by SDK `upsert_flow`/`push`; HTTP 201 means created, 200 means updated. |
| Delete flow | `DELETE /api/v1/flows/{flow_id}` | Deletes by ID. |
| Upload/import | `POST /api/v1/flows/upload/` | Uploads Langflow-compatible JSON; target project/folder must already exist if specified. |
| Download/export | `POST /api/v1/flows/download/` | Downloads selected flows as ZIP. |
| Public flow | `GET /api/v1/flows/public_flow/{flow_id}` | Public flow access path when enabled. |

Important distinctions:

- `flow_id` is a UUID in most CRUD URLs; `endpoint_name` is used for run-style URLs when a named endpoint is configured.
- In SDK `push`, the file's top-level `id` is used in the URL and intentionally omitted from the JSON body.
- Listing flows by project uses the folder/project query parameter accepted by the server. SDK naming uses `folder_id` because projects map to folders internally.

## Project Endpoints

Use `/api/v1/projects/` for project/folder management.

| Capability | Method/path | Notes |
| --- | --- | --- |
| List projects | `GET /api/v1/projects/` | Returns project IDs, names, and descriptions. |
| Create project | `POST /api/v1/projects/` | `ProjectCreate` supports `name`, optional `description`, `flows_list`, and `components_list`. Adding existing flows moves them into the project. |
| Read project | `GET /api/v1/projects/{project_id}` | Returns project details and flows. |
| Update project | `PATCH /api/v1/projects/{project_id}` | Only sent fields update. |
| Delete project | `DELETE /api/v1/projects/{project_id}` | Deletes by ID. |
| Export project | `GET /api/v1/projects/download/{project_id}` | Downloads all flows as a ZIP. |
| Import project | `POST /api/v1/projects/upload/` | Uploads a project ZIP and returns created flows. |

SDK archive helpers limit extraction to avoid zip-bomb behavior. If implementing your own client, apply similar limits before writing files.

## Flow Run And Webhook Endpoints

Use `/api/v1/run/{flow_id_or_name}` to execute a flow by UUID or endpoint name.

Basic JSON body fields:

```json
{
  "input_value": "Tell me something interesting",
  "input_type": "chat",
  "output_type": "chat",
  "tweaks": null,
  "stream": false
}
```

Additional documented run parameters can include `output_component` and `session_id` depending on endpoint usage and generated examples. If using the Python SDK, unsupported fields are not present in `RunRequest`; use raw HTTP when you need fields outside the SDK model.

Streaming:

- The documented REST examples use `?stream=true` on the run URL.
- The Python SDK sends `stream=True` in the JSON body for `client.stream(...)` and parses newline-delimited JSON event lines.
- Events include `add_message`, `token`, `end_vertex`, `end`, and `error`.
- `token` events carry incremental text in `data.chunk`.
- `end` events carry final result data in `data.result` when available.

Webhook runs use `/api/v1/webhook/{flow_id_or_name}` and are intended for flows with a Webhook component. The API access pane in Langflow can generate a suitable webhook curl command for a specific flow.

Deprecated trigger endpoints include `/process` and `/predict`; prefer `/run`.

## Response Shapes

`RunResponse` shape used by the SDK:

```json
{
  "session_id": "chat-123",
  "outputs": [
    {
      "results": {},
      "artifacts": {},
      "outputs": [
        {
          "results": {
            "message": {
              "text": "Hello from Langflow"
            }
          }
        }
      ]
    }
  ]
}
```

Robust clients should not assume every component returns `results.message.text`. The SDK checks `results.message.text` first and then direct `results.text` inside component outputs.

Stream line examples:

```json
{"event":"token","data":{"chunk":" Hello","id":"message-id"}}
{"event":"end","data":{"result":{"session_id":"chat-123","outputs":[]}}}
{"event":"error","data":{"error":"component failed"}}
```

HTTP errors are separate from event-level `error` events. A `401` response should be handled as authentication failure before parsing stream chunks; an event with `event="error"` means the server accepted the stream but the flow reported a runtime error.

## Python SDK Versus Raw HTTP

Prefer the Python SDK when:

- You need typed models for `Flow`, `Project`, `RunRequest`, or `RunResponse`.
- You want typed exceptions for auth, validation, not found, connection, and generic HTTP failures.
- You need push/pull normalization and project archive safety checks.
- You are writing tests with `httpx` mock transports.

Use raw HTTP when:

- You need a field not yet represented in the SDK model, such as a newly documented run parameter.
- You are validating generated curl/Python/JavaScript docs examples exactly.
- You are implementing a non-Python client against the OpenAPI spec.

Minimal raw run request:

```bash
curl -sS -X POST "${LANGFLOW_URL:-http://localhost:7860}/api/v1/run/${FLOW_ID}" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${LANGFLOW_API_KEY}" \
  -d '{"input_value":"Hello","input_type":"chat","output_type":"chat","tweaks":null}'
```

Do not put real API keys in shell history for shared terminals; prefer environment variables or a secrets manager.

## TypeScript Client Notes

The documented TypeScript client package is `@datastax/langflow-client`:

```bash
npm install @datastax/langflow-client
```

Basic usage:

```ts
import { LangflowClient } from "@datastax/langflow-client";

const client = new LangflowClient({ baseUrl: "http://localhost:7860", apiKey: process.env.LANGFLOW_API_KEY });
const response = await client.flow("flow-id-or-endpoint").run("Is anyone there?");
console.log(response.chatOutputText());
```

Streaming usage:

```ts
const events = await client.flow("flow-id-or-endpoint").stream("Hello", {
  session_id: "test-session",
  tweaks: { model_name: "gpt-4o-mini" },
});
for await (const event of events) {
  if (event.event === "token") process.stdout.write(event.data.chunk ?? "");
}
```

Keep TypeScript examples aligned with the REST contract. The TypeScript package is external to this repository; do not assume its implementation details beyond documented constructor and flow methods unless you inspect that package separately.

## API Example Validation Strategy

Safe validation order for generated API snippets:

1. **Offline syntax:** parse Python and JavaScript snippets for syntax, shell snippets for obvious variable placeholders, and JSON fixtures with `json.loads`.
2. **OpenAPI route check:** confirm method/path pairs exist in the relevant OpenAPI spec.
3. **Model check:** validate Python payloads against SDK models when they correspond to `FlowCreate`, `FlowUpdate`, `ProjectCreate`, `ProjectUpdate`, or `RunRequest`.
4. **Dry-run review:** ensure examples read credentials from environment variables and do not hard-code secrets.
5. **Live smoke only when requested:** run against a disposable local/test Langflow server with a known API key and non-credentialed flow. Avoid provider-backed flows unless the user explicitly supplies credentials.

Signals to report:

- Missing OpenAPI path or method means docs/client drift.
- `422` means request body schema mismatch or missing required flow component input.
- `401`/`403` means API key/auth policy problem, not payload shape.
- `404` means wrong UUID/endpoint name or route mismatch.
- `500` means accepted request reached backend but server/runtime failed; inspect server logs and flow component errors.
