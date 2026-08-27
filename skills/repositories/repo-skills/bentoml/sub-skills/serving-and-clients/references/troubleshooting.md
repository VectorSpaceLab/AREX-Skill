# Serving And Client Troubleshooting

## Wrong Import Target

Symptoms:

- `bentoml serve` cannot import a module or find the service object/class.
- Serving works from one directory but not another.

Fixes:

- Use an explicit target such as `service.py:Summarization`, `service:svc`, or a valid Bento tag.
- Pass `--working-dir` to the directory from which the target should import.
- Confirm service-authoring syntax in `../../service-authoring/SKILL.md`; this sub-skill assumes the service itself is valid.
- If serving a Bento directory, ensure it contains a valid `bentofile.yaml` with a service field or is a built Bento directory.

## Port Conflicts

Symptoms:

- Server fails to bind.
- A client reaches an unexpected old service.

Fixes:

- Change `--port` or `BENTOML_PORT`.
- Use separate ports for HTTP and gRPC servers.
- Check whether another process is already listening before retrying.

## Readiness Timeout

Symptoms:

- `SyncHTTPClient(...)` raises `ServiceUnavailable: Server is not ready after ... seconds`.
- `client.is_ready()` returns `False`.

Fixes:

- Increase `server_ready_timeout` during cold model loading.
- Verify `GET /readyz` manually.
- Check server logs for startup hook, dependency import, or model-loading failures.
- Pass `server_ready_timeout=0` only when deliberately skipping readiness waiting.

## Wrong Endpoint Names

Symptoms:

- `NotFound: Endpoint ... not found`.
- `AttributeError` for `client.some_method`.
- curl path works but Python method name differs, or the reverse.

Fixes:

- Fetch `/schema.json` and inspect each route’s `name` and `route`.
- Use `client.call("name", ...)` when dynamic names are easier than attributes.
- Remember that `@bentoml.api(route=...)` can change the HTTP path independently of the endpoint name.

## Request Payload Schema Errors

Symptoms:

- `TypeError: Arguments not found in endpoint ...`.
- `TypeError: Missing required arguments in endpoint ...`.
- HTTP 400/422-style validation errors.
- gRPC `INVALID_ARGUMENT` for descriptor mismatches.

Fixes:

- Match kwargs to the endpoint input schema from `/schema.json`.
- For root-input APIs, pass one positional value and no kwargs.
- For file fields, pass file paths/URLs/file-like values through the Python client or use multipart fields in curl.
- For gRPC, use generated BentoML message fields and valid descriptor types; malformed JSON bytes, wrong ndarray dtype/shape, and wrong file kind are rejected.

## Auth Token Errors

Symptoms:

- 401/403 responses from protected endpoints.
- Local code unexpectedly sends stale credentials.

Fixes:

- Pass `token=` explicitly for the target service.
- Clear or update `BENTO_CLOUD_API_KEY` if it is not meant for this server.
- Use local unauthenticated HTTP serving for development when possible.

## Missing gRPC Extra

Symptoms:

- Import errors around `grpc`, generated stubs, or gRPC health modules.
- `serve-grpc` fails before the server starts.

Fixes:

- Install BentoML with gRPC support in the active environment.
- Prefer HTTP serving if the caller does not specifically need gRPC descriptors or gRPC clients.
- On Windows, use `bentoml serve-grpc --development` for local testing.

## Async Client Lifecycle

Symptoms:

- Resource warnings about unclosed clients.
- Hanging event loop shutdown.
- Connections remain open after a script completes.

Fixes:

- Use `async with bentoml.AsyncHTTPClient(url) as client:`.
- If not using a context manager, call `await client.close()`.
- Do not share one async client across unrelated event loops.

## Streaming And WebSocket Confusion

Symptoms:

- Code waits forever for a streaming endpoint.
- A WebSocket path returns normal HTTP errors.

Fixes:

- Iterate streaming HTTP results chunk by chunk.
- Inspect `/schema.json` for `is_stream` on endpoint outputs.
- Use a WebSocket client library for `@app.websocket` routes; BentoML’s Python HTTP clients do not implement WebSocket connections.
- Combine the ASGI mount path and endpoint path, for example `/chat` plus `/ws` becomes `ws://host/chat/ws`.
