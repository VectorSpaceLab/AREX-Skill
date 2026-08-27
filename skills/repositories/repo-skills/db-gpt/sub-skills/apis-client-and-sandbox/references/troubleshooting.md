# Troubleshooting and safety matrix

Diagnose in order: URL construction → connectivity → authentication → request validation → response envelope/status → dependency/service health → cleanup. Capture method, path, status, redacted body, timeout, resource ID, and whether the call was mock, local, or live.

## Client and HTTP failures

| Symptom | Likely cause | Safe response |
|---|---|---|
| `ValueError` constructing `Client` | `api_base` lacks a scheme/host or contains a malformed URL | Use a full `http://` or `https://` base such as `http://localhost:5670/api/v2`; construction alone does not test reachability. |
| Connection refused / DNS / timeout | Web server is not running, wrong host/port, proxy/network boundary, or overloaded service | Check the approved service status and deployment configuration. Do not start a service or retry mutating calls automatically. |
| HTTP 401 / `invalid_api_key` | Missing bearer token, wrong key, or service key list enabled | Load the key from an approved secret source and send exactly `Authorization: Bearer ...`; never print it. If the service has no configured key list, auth may be permissive. |
| HTTP 404 for datasource/space/document/flow/app/file | Wrong prefix, wrong ID, resource deleted, or resource belongs to another deployment | Confirm the mounted route in `/docs`, list or query the resource, and use the returned identifier. Do not substitute a name for an ID. |
| HTTP 400/422 | Missing required field, wrong type, invalid mode, malformed JSON, or wrong form/multipart shape | Compare the request with the endpoint schema. For v2 chat, `model` and `messages` are required; non-normal modes also need `chat_param`. |
| HTTP 409 or `success: false` conflict | Duplicate resource, stale update, dependency conflict, or operation already in progress | Re-read current state, decide whether the operation is idempotent, and update/delete only with explicit approval. Do not blindly retry create. |
| HTTP 5xx / `success: false` | Server-side exception or unavailable backend | Preserve the error code/message, inspect server logs through the operator, and check the dependent database/model/vector/file service. A parsed JSON body is not proof of success. |
| Response body is not JSON | Streaming response, proxy error page, or server crash | Inspect `Content-Type` and status before parsing. Preserve a bounded/redacted text excerpt. |
| Python wrapper raises an odd `ClientException` | CRUD wrappers catch broad exceptions and pass the message as the first positional constructor argument | Treat `.status` as potentially a message, not necessarily an integer HTTP status. Preserve the original exception/status from the raw response in diagnostics where possible. |
| Stream hangs or parsing fails | No `[DONE]`, proxy buffering, malformed `data:` line, or backend failure event | Set a finite timeout, consume only valid `data:` records, stop at `[DONE]`, and surface malformed/non-200 output as an error. Do not concatenate an error JSON object into assistant text. |
| Client object keeps resources open | Missing `aclose()` or loop shutdown | Close it in `finally`: `await client.aclose()`. Prefer explicit async close over relying on the `atexit` hook. |

### URL and helper mismatches

- Generic client service methods append `/serve` to `api_base`. With `api_base=http://localhost:5670/api/v2`, `client.get("/datasources")` targets `/api/v2/serve/datasources`.
- `head()` is an implementation exception and uses `api_base + path` without inserting `/serve`.
- `post_param()` sends query parameters. It is not a JSON-body method.
- The client `create_document()` helper uses query parameters, but the 0.8.1 server document-create route expects multipart form fields. Use raw multipart HTTP after checking the deployed schema.
- The client `update_flow()` helper sends a collection PUT, while the v2 flow service is UID-addressed (`PUT /flows/{uid}`). Use a raw UID-addressed request unless a compatibility route is confirmed.
- Client `chat()` returns a typed response only for HTTP 200; its non-200 branch returns decoded JSON. `chat_stream()` similarly yields decoded non-200 JSON when possible. Callers must validate shape and status.

## Service composition failures

### Datasource

- `GET /api/v2/serve/datasource-types` is catalog discovery, not a connectivity test. Call `POST /api/v2/serve/datasources/test-connection` with the correct dynamic or compatibility request before creating a remote datasource.
- A local SQLite path must exist in the process-visible environment and have appropriate permissions. A host path inside a client request is not automatically visible to a remote server/container.
- MySQL, PostgreSQL, graph, and other connectors need both the selected optional Python driver and a reachable external service. Mark them blocked/optional if those prerequisites were not provisioned.
- If knowledge chat says a space is missing, check the exact `chat_param` space identifier/name and query the knowledge service. Do not create a duplicate space in response to a transient read failure.

### Knowledge and documents

- Space creation and document upload are separate operations. Create/verify the space first; send `doc_name`, `doc_type`, and `space_id` as multipart fields for document creation.
- A document can exist but not be indexed. Sync requires a document/space relationship and may require an embedding model, vector store, or chunk configuration. Route those backend details to the data/RAG skill.
- `POST /spaces/{id}/retrieve` returns 404 when the space is absent. A successful retrieve route still does not prove that its index is populated.
- `DELETE /spaces/{id}` and document deletion may leave files or vector artifacts depending on the service implementation. Verify cleanup separately and do not assume destructive deletion is fully cascading.

### Flow and app

- A flow/app list can be empty because of pagination, user/system filters, or a different metadata database. Resolve one UID/app code before invoking chat.
- Flow command execution requires exactly one matching flow, one HTTP trigger, and a usable trigger method/path. Multiple matches, missing metadata/triggers, and non-HTTP triggers are explicit errors.
- App chat is streaming-only in v2. If a client requests `chat_app` with `stream=false`, correct the request rather than retrying.
- A flow or app API response does not validate the provider, agent, datasource, knowledge, or tool dependencies used during execution. A later 400/5xx can be an integration failure.
- Dynamic model discovery or model CLI help can contact a controller and return 502 when that controller is unavailable. Use static request/schema checks when no controller is approved.

### Files and uploads

- The file service uses opaque `bucket` + `file_id`; a local file path is not a file ID. Upload first, retain the returned metadata, then download/read by the returned identifier.
- Metadata batch requests must supply exactly one of `uris` or `bucket_file_pairs`; an empty or both-filled request is invalid.
- The file route streams downloads using configured chunks. Backend/local storage path and transfer timeout are configuration-dependent; there is no universal route-level upload limit established here.
- The app skill import endpoint has a 50 MiB download limit. Archive extraction rejects traversal entries, and remote imports require explicit trust/approval. The current 0.8.1 single-file skill upload path does not reliably reject traversal-shaped filenames (the native traversal test fails); patch or wrap it with basename/containment validation before any temporary write rather than assuming the endpoint is safe.
- Python upload and agent-file download enforce path containment. Treat returned absolute server paths as opaque diagnostics; do not send arbitrary paths back to a download endpoint.
- On an upload failure, check whether a temporary file was created and remove only files inside an approved temporary root. Do not delete a shared workspace based solely on a client-supplied filename.

## Sandbox failures

| Symptom | Meaning | Recovery |
|---|---|---|
| Auto factory says no container runtime available | Docker/Podman/Nerdctl was not usable and local fallback is disabled | Install/configure an approved container backend or explicitly approve local host execution. Do not silently enable local mode. |
| Explicit `local` rejected | `SANDBOX_ALLOW_LOCAL_RUNTIME` was false when the factory module loaded | Set the opt-in before importing the factory in an isolated process. Reassess the host-risk approval; local is not container isolation. |
| Docker selected but session start fails | SDK/daemon permission, image missing, image pull blocked, invalid working directory, or resource limit | Check daemon access, image availability, and approved limits. Do not fall back to local merely to make the task pass. |
| Podman/Nerdctl session fails | CLI absent, image unavailable, name/port collision, or CLI command failure | Preserve the stderr and check the selected runtime directly under operator control. Nerdctl does not currently enforce the network-disabled flag. |
| `supports_language` false or unknown language | Runtime cannot provide the requested interpreter/image | Select a supported language or provision the backend/image; do not use a generic `cat` fallback for untrusted code. |
| Code rejected before execution | Pattern-based `SecurityUtils` found a known dangerous operation | Review and rewrite the code using approved APIs. Do not bypass the check with obfuscation; the scanner is intentionally incomplete. |
| Code times out / process remains | Execution exceeded the session timeout or child process tree did not terminate cleanly | Record `TIMEOUT`/error, kill descendants through the runtime, destroy the session, and verify no process or artifact remains. |
| Dependency installation fails | Local runtime does not implement nonempty dependency installation; container install needs package/network access or unsupported language | Prefer a prebuilt, pinned image. Never install arbitrary model-provided packages on the host. Container pip/npm installation is a network and supply-chain operation. |
| File retrieval fails or leaks a path | Missing session/file, invalid filename, or runtime-specific artifact format | Use a known relative artifact name and active session. Validate containment and decode container base64 only after checking status. |
| Session survives an error | Caller omitted `destroy_session` or cleanup task was not awaited | Always destroy in `finally`, list sessions after cleanup, and run idle cleanup as a secondary control. |
| `network_disabled` appears set but network is reachable | Local and current Nerdctl paths do not provide the same network isolation as Docker/Podman | Treat the execution as network-capable; stop and use a verified isolated container if no-network is required. |

### Local runtime risk model

The local runtime creates a subprocess on the host. Its checks are string-pattern warnings, not an AST policy, syscall filter, container, namespace, or network sandbox. It updates process environment variables, may use a custom host working directory, and intentionally leaves custom directories in place on stop. Use it only for approved development/test fixtures with non-sensitive data. Never claim that a passing local smoke test proves production isolation.

## Mock, local, and live boundary

- **Mock:** use a response double and recorded method/path/payload. This proves helper serialization and error handling only.
- **Local package:** import schemas/routers, inspect signatures, construct a temporary local runtime, or register sandbox routes on an existing in-memory FastAPI app. This proves package wiring only.
- **Live local service:** call an explicitly running DB-GPT instance at a configured origin. It may mutate metadata, files, flows, models, or sandboxes and requires approval.
- **External service:** model providers, remote databases, vector/graph stores, container daemons/images, registries, and remote skill URLs require separate credentials/network/service checks. They are not covered by CPU imports or mock tests.

Report which boundary was tested. Never promote a mock or import result to a live integration claim.
