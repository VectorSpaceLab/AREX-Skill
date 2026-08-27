# LitServe server troubleshooting

Use this guide for general `LitAPI`/`LitServer` serving issues. Route OpenAI chat or
embeddings issues to `openai-specs`, and MCP tool/server issues to `mcp`.

## Quick diagnostic checklist

1. Confirm the server file imports LitServe in the active environment:
   `python -c "import litserve as ls; print(ls.__version__)"`.
2. Start locally with explicit safe defaults:
   `host="127.0.0.1"`, `port=8000`, `accelerator="cpu"`, `devices=1`, `workers_per_device=1`.
3. Check `GET /health` and `GET /info` before debugging `/predict`.
4. Confirm the request content type matches the `decode_request` contract.
5. Check auth headers before interpreting a `401`/`403` as a model error.
6. If the server crashes during startup, inspect `setup(device)` first.

## Invalid `api_path`

Symptoms:

- `ValueError: api_path must start with '/'`.
- `ValueError: api_path /... is already in use by ...`.
- A route is missing from `/docs` or returns `404`.

Causes and fixes:

- Use `api_path="/predict"`, not `"predict"`.
- In multi-endpoint servers, every API must have a unique path.
- Do not use reserved paths `/health` or `/info` for model APIs.
- Keep spec-owned paths out of server-basics. OpenAI routes such as
  `/v1/chat/completions` and `/v1/embeddings` belong to `openai-specs`.
- If migrating old code, move `api_path` from `LitServer(..., api_path=...)` to
  `MyAPI(api_path=...)`.

## Invalid health, info, or shutdown path

Symptoms:

- `ValueError: healthcheck_path must start with '/'`.
- `ValueError: info_path must start with '/'`.
- `ValueError: shutdown_path must start with '/'`.

Fix:

```python
server = ls.LitServer(
    api,
    healthcheck_path="/v1/health",
    info_path="/v1/info",
    shutdown_path="/v1/shutdown",
    enable_shutdown_api=True,
)
```

All custom internal paths must start with `/`.

## Port out of range or invalid host

Symptoms:

- `ValueError: port must be a value from 1024 to 65535 but got ...`.
- `ValueError: host must be '0.0.0.0', '127.0.0.1', or '::' but got ...`.

Fixes:

- Use a port between `1024` and `65535`, for example `8000` or `8080`.
- Use `host="127.0.0.1"` for local-only development.
- Use `host="0.0.0.0"` for Docker or remote access.
- Use `host="::"` for IPv6 binding.
- If the port is already in use, stop the other process or choose another valid port.

## Middlewares must be a list

Symptom:

```text
ValueError: middlewares must be a list of tuples ...
```

Wrong:

```python
server = ls.LitServer(api, middlewares=(RequestIdMiddleware, {"length": 5}))
```

Right:

```python
server = ls.LitServer(api, middlewares=[(RequestIdMiddleware, {"length": 5})])
```

A middleware entry can also be a bare callable/class when no kwargs are needed:

```python
server = ls.LitServer(api, middlewares=[HTTPSRedirectMiddleware])
```

## Payload too large

Symptoms:

- HTTP `413`.
- Response detail: `Payload too large`.
- Upload fails before `predict` runs.

Fixes:

- Increase or remove `max_payload_size`:

  ```python
  server = ls.LitServer(api, max_payload_size=50 * 1024 * 1024)
  ```

- Make sure clients are not sending unexpectedly large multipart bodies.
- Decode uploaded files to the smallest useful representation in `decode_request`.
- Do not use this sub-skill's examples for large benchmark payloads.

## Multipart or form parsing fails

Symptoms:

- Form requests fail while JSON requests work.
- FastAPI/Starlette complains about form parsing support.
- `request["input"]` is missing for file uploads.

Fixes:

- Install `python-multipart` in the serving environment.
- For multipart files, send `curl -F 'input=@file.txt'` and read
  `request["input"].file` in `decode_request`.
- For URL-encoded forms, send the correct content type and `-d 'input=value'`.
- Annotate the hook as `decode_request(self, request: Request)` when expecting form or
  multipart mappings.

## Auth header mismatch

Symptoms:

- HTTP `401` or `403`.
- Detail contains `Invalid API Key`, `Bad token`, or a FastAPI auth dependency error.

Global API key fixes:

- If `LIT_SERVER_API_KEY` is set, send the exact header:

  ```bash
  curl -H 'X-API-Key: <value>' ...
  ```

- Environment variables are read when the server module is imported/started; restart the
  server after changing them.

Custom bearer auth fixes:

- Send `Authorization: Bearer <token>`.
- Check that the API's own `authorize` method is attached to the intended route.
- In multi-endpoint servers, verify each API uses the intended token; one route can be
  open while another is protected.

## Shutdown token issues

Symptoms:

- `POST /shutdown` returns `401`.
- Detail mentions `Invalid Bearer token for Shutdown API`.
- The server logs a generated shutdown key.

Fixes:

- Set a stable token before startup:

  ```bash
  export LIT_SHUTDOWN_API_KEY='shutdown-secret'
  ```

- Enable the endpoint explicitly:

  ```python
  server = ls.LitServer(api, enable_shutdown_api=True)
  ```

- Call it with:

  ```bash
  curl -X POST http://127.0.0.1:8000/shutdown \
    -H 'Authorization: Bearer shutdown-secret'
  ```

- Do not rely on the generated token in production; it is emitted to logs and changes when
  regenerated.

## Worker readiness and health failures

Symptoms:

- `GET /health` returns `503 not ready`.
- Startup raises `RuntimeError: One or more workers failed to start. Shutting down LitServe`.
- Requests hang until timeout.

Likely causes:

- `setup(device)` raised an exception.
- Model weights or external resources are missing.
- `health()` returns `False` or raises.
- No worker has reached the ready state yet.
- `batch_timeout` is larger than `timeout`.

Fixes:

- Start with `accelerator="cpu"`, `devices=1`, `workers_per_device=1`, and a tiny model.
- Move heavy loading from `__init__` into `setup(device)`.
- Add explicit logging inside `setup` and `health`.
- Increase `timeout` for slow models, or use `timeout=False`/`timeout=-1` only when you
  intentionally want no request timeout.
- Keep `batch_timeout < timeout`.
- For flaky workers, consider `restart_workers=True`, but first fix deterministic setup
  failures.

## Request timeout or slow responses

Symptoms:

- Client times out.
- Long-running `predict` blocks other requests.
- Batches do not fill under load.

Fixes:

- Increase `LitServer(timeout=...)` for slow models.
- Use `enable_async=True` and async methods for I/O-bound work.
- Use batching for models that benefit from batched computation; test with concurrent
  requests.
- Increase `workers_per_device` only if memory allows multiple model replicas.
- Increase `num_api_servers` for HTTP handling capacity, not as a substitute for model
  workers.
- Use streaming for operations where users need incremental output.

## `enable_async=True` raises validation errors

Symptom:

```text
Async validation failed:
- predict must be an async generator or async function when enable_async=True
```

Fix:

```python
class AsyncAPI(ls.LitAPI):
    async def decode_request(self, request):
        return request["input"]

    async def predict(self, x):
        return x * x

    async def encode_response(self, output):
        return {"output": output}

api = AsyncAPI(enable_async=True)
```

If only `decode_request` or `encode_response` are sync, LitServe warns and asyncifies
those hooks; sync `predict` is not accepted with async enabled.

## Batched output is split incorrectly

Symptoms:

- Each request receives one character/key instead of one prediction.
- Warnings mention strings, dictionaries, or sets returned by batched `predict`.
- `unbatch` raises `Default implementation ... was not found` in manual tests.

Fixes:

- Return a list-like output with one element per input.
- For dictionary outputs, return `[{...}, {...}]`, not `{key: [values...]}`.
- Implement `unbatch` when model output needs custom splitting.
- Call batching through a real `LitServer` run/wrap path; default unbatch setup is prepared
  during server pre-setup.

## Streaming response is malformed

Symptoms:

- Client buffers until the end.
- JSON chunks are hard to parse.
- Streaming route behaves like regular JSON.

Fixes:

- Set `stream=True` on the `LitAPI` constructor.
- Make `predict` yield items and `encode_response` yield chunks.
- Use `curl -N` or an HTTP client that reads incrementally.
- Yield dicts or Pydantic models for newline-delimited JSON chunks.
- Do not use OpenAI streaming schemas here; route to `openai-specs`.

## `client.py` already exists

Symptom:

- `server.run(generate_client_file=True)` does not update `client.py`.

Cause:

- LitServe intentionally skips generation if `client.py` exists in the current working
  directory.

Fixes:

- Delete or rename the existing `client.py` before rerunning.
- Change to a clean working directory.
- Disable generation in production entrypoints:

  ```python
  server.run(generate_client_file=False)
  ```

## Dockerfile generation fails

Symptoms:

- `FileNotFoundError: Server file ... must be in the current directory`.
- Dockerfile lacks model dependencies.
- GPU container starts without GPU access.

Fixes:

- Run `litserve dockerize server.py` from the directory containing `server.py`.
- Add a `requirements.txt` before dockerizing, or edit the generated Dockerfile manually.
- For GPU scaffolding, pass `--gpu` and run the container with `--gpus all` on a host with
  NVIDIA container support.
- Keep secrets out of the Dockerfile; inject them through environment variables or your
  deployment platform.

## Lightning SDK auto-install failure

Symptoms:

- The `lightning` entry point prints `Failed to install lightning-sdk`.
- It tried pip and/or uv but deployment did not start.
- It prints `Error importing lightning_sdk CLI`.

Fixes:

- Install manually in the serving environment:

  ```bash
  python -m pip install -U lightning-sdk
  ```

- If using uv-only environments:

  ```bash
  uv pip install -U lightning-sdk
  ```

- Retry the intended command, for example `lightning deploy server.py --cloud`.
- If import still fails, verify the active Python environment is the one used by the
  `lightning` entry point.

## Logger warnings or missing metrics

Symptoms:

- Warning: logging attempted without a configured logger.
- Custom logger does not process events.
- `RequestTracker` logs `Active requests: None`.

Fixes:

- Pass a `Logger` instance or list of instances to `LitServer(loggers=...)`.
- Call `self.log(key, value)` only after the logger queue is configured by the server.
- Make logger instances pickleable or lightweight enough to recreate by class.
- Use `track_requests=True` when using `RequestTracker` and active request counts.

## `/info` serialization fails

Symptom:

- `ValueError: model_metadata must be JSON serializable.`

Fix:

Use plain dictionaries, lists, strings, numbers, booleans, and nulls:

```python
server = ls.LitServer(api, model_metadata={"name": "demo", "version": "1.0"})
```

Do not pass classes, functions, open files, or model objects as `model_metadata`.

## Multiple endpoints collide

Symptoms:

- `ValueError: api_path /api1 is already in use by ...`.
- `ValueError: api_path /health is already in use by LitServe healthcheck`.
- `workers_per_device contains unknown api_path values`.

Fixes:

- Give each API a unique leading-slash path.
- Avoid `/health` and `/info`.
- Keep `workers_per_device` list length equal to the number of APIs, or use a mapping with
  exact known paths.

## Excluded benchmark and accelerator paths

This sub-skill intentionally excludes:

- Throughput benchmark suites.
- FastAPI parity benchmark harnesses.
- Torch, CUDA, transformer, and vision benchmark workflows.

Reason: these paths are benchmark- or accelerator-heavy, introduce optional dependencies,
and were not selected for the verified CPU server-basics scope. Use this sub-skill for
application-serving workflows; request a future extension for benchmark or accelerator
parity work.
