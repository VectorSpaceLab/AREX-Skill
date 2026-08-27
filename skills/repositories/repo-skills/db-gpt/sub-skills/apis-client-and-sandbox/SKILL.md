---
name: apis-client-and-sandbox
description: "Operate DB-GPT 0.8.1 through its Python client, HTTP service APIs,
  application routes, file and app workflows, and explicitly bounded sandbox
  runtimes."
metadata:
  disco-role: operating
license: Apache 2.0
disable-model-invocation: true
---

# APIs, client, and sandbox

Use this route when a task names `dbgpt-client`, `dbgpt_serve`, `dbgpt-app` HTTP/OpenAPI, datasource or knowledge CRUD, AWEL flow service calls, app/skill/file uploads, model service endpoints, or `dbgpt-sandbox`. It is the integration boundary: it teaches request construction, service composition, response/error interpretation, and safe execution boundaries. It does **not** replace the data/RAG, agent/AWEL, or model-provider routes.

## Route quickly

- **Python client or CRUD:** load [client-api-reference.md](references/client-api-reference.md). Use the async helpers for the operations they actually cover; use the endpoint reference for operations absent from the client or where its legacy helper does not match the server schema.
- **HTTP route, service prefix, auth, or multipart request:** load [service-endpoints.md](references/service-endpoints.md).
- **Sandbox session, runtime selection, code execution, or artifact retrieval:** load [sandbox-workflows.md](references/sandbox-workflows.md), then apply the safety boundary in [troubleshooting.md](references/troubleshooting.md).
- **Failure or uncertain live integration:** start with [troubleshooting.md](references/troubleshooting.md). Do not infer a live service, model, database, container image, credential, or network from a successful import.

## Operating contract

### Inputs

Establish these before making a request or executing code:

1. **Target surface:** client helper, raw HTTP, app OpenAPI, `dbgpt-serve`, or standalone sandbox API.
2. **Base URL and version:** the client expects a full URL such as `http://localhost:5670/api/v2`; do not give it only a host or a URL ending at `/api` unless the operation is intentionally raw HTTP.
3. **Authentication:** use `DBGPT_API_KEY` or an explicitly supplied key only when the server is configured with API keys. Never place a real key in a script, fixture, log, or prompt. The client sends `Authorization: Bearer <key>` when a key is present.
4. **Dependency order and ownership:** create or verify a datasource before using it in data chat; create or verify a knowledge space before creating/syncing documents; resolve a flow/app/model identifier before running it. Use the server's returned identifier, not a guessed name.
5. **Execution boundary:** default to mock/local schema checks. A live call requires an explicitly reachable server and approved credentials; a sandbox container requires an available image/runtime. No helper in this route starts a service by default.

### Workflow

1. **Discover without side effects.** Import only the public package needed for the operation. For a live deployment, use its `/docs` or OpenAPI description to confirm the exact mounted prefix and request shape. A safe health or test-auth request is optional and still counts as a live request.
2. **Build the smallest valid request.** Validate required fields, identifiers, content type, pagination, and whether data belongs in JSON, query parameters, form fields, or multipart files. Keep database passwords, bearer tokens, and provider keys out of diagnostics.
3. **Execute asynchronously and close resources.** `Client` uses `httpx.AsyncClient`; use `await client.aclose()` in a `finally` block. Treat stream iterators as one-shot and consume `data: [DONE]` for OpenAI-style SSE.
4. **Check both transport and envelope.** Service endpoints generally return a DB-GPT `Result` envelope with a `success` flag and `data`, while some failures are HTTP 400/401/404/5xx. Do not call a response successful merely because JSON parsed.
5. **Record identifiers and cleanup.** Preserve response IDs, flow UIDs, file IDs, and sandbox session IDs. Delete temporary uploads, flow/session resources, and test fixtures when the operation finishes or fails.
6. **Escalate boundary failures.** Distinguish malformed request (usually 400/422), missing/invalid key (401), missing entity (404), conflict/dependency (409 or an unsuccessful `Result`), service failure (5xx), connection/timeout, and missing optional backend. See the troubleshooting reference.

## High-value facts

- DB-GPT application defaults to web host `0.0.0.0` and port `5670`; the standard API base is `http://localhost:5670/api/v2`.
- `Client(api_base=None, api_key=None, version="v2", timeout=120)` reads `DBGPT_API_BASE` and `DBGPT_API_KEY`. The URL must have a scheme and network location. A timeout of `None` creates an unlimited `httpx` timeout and should be used only deliberately.
- The client appends `/serve` for its generic service methods. Thus `client.get("/datasources")` targets `<api_base>/serve/datasources`, and `post_param` sends query parameters rather than a JSON body.
- Client CRUD helpers are async functions in `dbgpt_client.datasource`, `dbgpt_client.knowledge`, `dbgpt_client.flow`, and `dbgpt_client.app`; only `Client` and `ClientException` are exported from the package root.
- The v2 chat request requires `model` and `messages`. `chat_mode` is normally `chat_normal`; specialized modes require `chat_param`: `chat_app`, `chat_flow`, `chat_knowledge`, `chat_data`, `chat_with_db_qa`, and `chat_dashboard`. Non-streaming app chat is rejected by the v2 route. Flow and app chat normally stream.
- Application OpenAPI v1 routes are mounted under `/api`; v2 chat is `/api/v2/chat/completions`. Stable service routes are mounted under `/api/v2/serve/...`; a few compatibility v1 routes remain and are not automatically compatible with v2.
- `dbgpt-serve` components are registered into one FastAPI application. A health response indicates a route is alive, not that its datasource, model, vector store, file backend, or sandbox dependency is healthy.
- Sandbox auto-selection prefers Docker, then Podman, then Nerdctl, and fails closed when no container backend is available. Host-local execution is an explicit opt-in and must never be described as container isolation.

## Boundaries and non-goals

- Route RAG loaders, chunking, embeddings, vector stores, connector-specific SQL, and retrieval implementation to `data-and-rag`.
- Route agent construction, tool packs, ReAct behavior, and AWEL graph topology to `agents-and-awel`; this route only covers calling a persisted flow or app over an API.
- Route provider credentials, model adapter installation, controller/worker deployment, GPU, CUDA, and VRAM to `models-and-serving`.
- Do not run an installer, start Uvicorn, launch a model, contact a provider, clone/import a remote skill, install sandbox dependencies, or provision an external database as an implicit validation step.
- Do not claim that a local sandbox is secure isolation. Its code check is a simple pattern check and its `network_disabled` setting is not host-network isolation in `LocalRuntime`.
- Do not put untrusted package names into shell-built dependency-install commands, pass secrets through sandbox environment variables, or return host file paths as if they were portable artifact URIs.

## Validation checklist

For a **client/API** change, validate without a live service where possible:

- `inspect.signature` and imports resolve for `Client`, `ClientException`, the target schema, and the target helper.
- A mocked response covers success, unsuccessful `Result`, malformed response, 401/404/409, and a transport/timeout failure.
- The asserted HTTP method and path match the mounted endpoint, and JSON/query/form/multipart placement is explicit.
- Streams parse only `data:` JSON events and stop at `[DONE]`; non-200 streams are failures, not assistant content.
- The async client is closed and no credential or external-service side effect occurs.

For a **sandbox** change, validate safely:

- `RuntimeFactory.create()` fails closed with container detection disabled and local opt-in absent.
- Explicit `local` fails unless both local opt-in controls were enabled before module initialization; an opted-in local factory reports `LocalRuntime`.
- A tiny local session can execute deterministic, non-I/O code, reject a known dangerous pattern, and remove its automatically created temporary directory on destroy.
- Missing image/runtime, timeout, process termination, dependency-install failure, and artifact cleanup are reported as bounded errors.

The bundled [sandbox_cli_wrapper.py](scripts/sandbox_cli_wrapper.py) validates request payloads and policy-shaped code locally. It never starts a server or executes the supplied code.

## Troubleshooting

Use the symptom-driven matrix in [troubleshooting.md](references/troubleshooting.md). Preserve the original HTTP status, response body (with secrets redacted), request path, operation ID, and whether the failure occurred before or after the service boundary. Do not retry destructive create/delete or upload operations blindly; check idempotency and current resource state first.
