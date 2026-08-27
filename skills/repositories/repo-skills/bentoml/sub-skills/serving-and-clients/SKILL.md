---
name: serving-and-clients
description: "Serve BentoML services locally over HTTP or gRPC and call
  endpoints with Python clients, curl/OpenAPI, streaming, websocket clients, and
  operational serve flags."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BentoML Serving And Clients

Use this sub-skill when the user needs to run a BentoML service locally, choose HTTP versus gRPC serving, call service endpoints from Python or curl, inspect endpoint schemas, or debug client/serve failures. For defining `@bentoml.service` and `@bentoml.api`, use `../service-authoring/SKILL.md`. For `bentoml build`, containerization, and Bento packaging, use `../packaging-and-containerization/SKILL.md`. For metrics, logs, tracing, scaling, and runtime resource configuration, use `../observability-and-operations/SKILL.md`. For BentoCloud deployments and cloud endpoints, use `../cli-and-cloud/SKILL.md`.

## Local Serving

- Start HTTP serving with `bentoml serve SERVICE_TARGET`, where `SERVICE_TARGET` is an import target such as `service.py:Summarization`, a local Bento tag such as `fraud_detector:latest`, or a Bento directory.
- Prefer explicit source serving commands during development: `bentoml serve service.py:ServiceClass --working-dir . --development --reload --port 3000`.
- Production mode is the CLI default; use `--development` for local iteration because it uses one API worker and, with `--reload`, restarts on code/model-store changes.
- Set `--working-dir` whenever the service module is not in the current shell directory; this prevents import target failures caused by the wrong `sys.path`.
- Use `--host`, `--port`, `--api-workers`, `--backlog`, `--timeout`, and SSL flags for local server behavior; environment variables `BENTOML_HOST`, `BENTOML_PORT`, `BENTOML_API_WORKERS`, and `BENTOML_TIMEOUT` can also supply values.
- Use `bentoml serve-grpc SERVICE_TARGET` only when the caller needs gRPC; it is hidden in the CLI but implemented, supports reflection/channelz flags, and may require installing BentoML with gRPC dependencies.

See `references/cli-reference.md` and the bundled dry-run helper `scripts/serve_command_builder.py` for safe command construction.

## HTTP Client Calls

- Use `bentoml.SyncHTTPClient(url, token=None, timeout=30, server_ready_timeout=None)` for blocking Python calls and `bentoml.AsyncHTTPClient(...)` for async code.
- Prefer context managers so connections close cleanly: `with bentoml.SyncHTTPClient("http://localhost:3000") as client:` or `async with bentoml.AsyncHTTPClient("http://localhost:3000") as client:`.
- Client methods are created from the server’s `/schema.json`; call `client.<endpoint>(...)` when the endpoint name is a valid Python attribute or `client.call("endpoint_name", ...)` when it is dynamic.
- Match arguments to the service API signature. Normal structured inputs use keyword arguments such as `client.summarize(text="...")`; root-input APIs require exactly one positional argument.
- Set `server_ready_timeout` when connecting while a server is booting, and use `client.is_ready()` to check `/readyz` before sending expensive calls.
- For authenticated endpoints, pass `token="..."`; if omitted, the client reads `BENTO_CLOUD_API_KEY` and sends `Authorization: Bearer <token>` when available.

See `references/client-reference.md` and `scripts/inspect_service_client.py` for schema inspection without starting a server.

## Curl, OpenAPI, And Schema

- The local UI is available from the server root, the client schema is at `/schema.json`, readiness is at `/readyz`, and OpenAPI JSON is exposed under the docs route as `docs.json`.
- For JSON APIs, send `POST /<route>` with `Content-Type: application/json`; the hello-world endpoint shape is `curl -X POST http://localhost:3000/summarize -H 'Content-Type: application/json' -d '{"text":"..."}'`.
- If the API uses root input, the raw request body may be a scalar, bytes/text, or a serialized JSON value rather than an object with named fields.
- For files, the Python client switches to multipart when the schema contains file fields; with curl, mirror the schema’s content type and multipart field names.
- For endpoint-name confusion, inspect `/schema.json` first; API method names, custom `route=...` values, and visible HTTP paths can differ.

## Streaming And WebSockets

- A BentoML API that returns a Python generator or async generator is exposed as a streaming HTTP response; the Sync client returns an iterator and the Async client returns an async iterator for stream outputs.
- Iterate streaming results instead of forcing a single response value: `for chunk in client.generate(prompt="..."):` or `async for chunk in await client.generate(prompt="..."):` depending on the async method’s return.
- WebSocket endpoints are mounted through FastAPI/ASGI apps, usually with `@bentoml.asgi_app(app, path="/chat")`; the BentoML Python HTTP clients do not support WebSockets.
- Use a WebSocket library such as `websockets` and connect to the mounted path plus websocket route, for example `ws://localhost:3000/chat/ws`.
- Keep service-authoring details for ASGI mounting in `../service-authoring/SKILL.md`; this sub-skill focuses on calling and debugging the running server.

## gRPC Serving

- Use `bentoml serve-grpc SERVICE_TARGET --port 3000 --host 0.0.0.0` for local gRPC serving when the environment includes gRPC support.
- gRPC serving exposes BentoML’s generated service protocol and health service; tests use `grpc.health.v1.Health/Check` and generated BentoML stubs.
- Useful gRPC flags include `--enable-reflection`, `--enable-channelz`, `--max-concurrent-streams`, `--protocol-version v1|v1alpha1`, `--api-workers`, `--backlog`, and SSL cert/key/CA options.
- On Windows, production gRPC serving has limitations around `SO_REUSEPORT`; use `--development` for local testing or containerize on Linux for production-like behavior.

## Helper Scripts

- `scripts/serve_command_builder.py` builds shell-safe `bentoml serve` or `bentoml serve-grpc` commands and never starts a server unless a user copies the output.
- `scripts/inspect_service_client.py` requires an explicit URL, checks `/readyz` and `/schema.json`, and prints endpoint routes, input/output schemas, streaming flags, and task flags.
- Keep all script examples self-contained and avoid pointing runtime guidance at source-repo docs, tests, or local checkout paths.

## Troubleshooting Checklist

- Import target fails: use `module.py:ClassName` or `module:svc`, pass `--working-dir`, and confirm the module imports from that directory.
- Port conflict: change `--port`, clear the process occupying the port, or use a separate HTTP and gRPC port.
- Readiness timeout: increase `server_ready_timeout`, check `/readyz`, and verify expensive model loading or startup hooks are not failing.
- Wrong endpoint name: fetch `/schema.json`, then call the route’s `name` with `client.call(name, ...)` or the generated method.
- Request schema error: compare your kwargs to the endpoint input schema; root inputs take one positional argument and reject keyword arguments.
- Auth token error: pass `token=` explicitly or set `BENTO_CLOUD_API_KEY`; verify the endpoint actually expects BentoCloud-style bearer auth.
- Missing gRPC support: install the gRPC extra/dependencies before using `serve-grpc` or generated gRPC clients.
- Async lifecycle leak: use `async with bentoml.AsyncHTTPClient(...)` or call `await client.close()`.

For deeper failure mapping, see `references/troubleshooting.md`.
