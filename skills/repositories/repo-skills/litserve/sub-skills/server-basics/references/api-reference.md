# LitServe server API reference

This reference is self-contained for LitServe `0.2.18` server workflows.

## Import surface

```python
import litserve as ls

# Common exports
ls.LitAPI
ls.LitServer
ls.Callback
ls.Logger
ls.configure_logging
ls.Request
ls.Response
```

The verified package imports cleanly. The `litserve` CLI and `litserve dockerize`
help are available. `ImageInput`, `ImageOutput`, and MCP imports were also verified
with the inspection extras, but OpenAI-compatible and MCP endpoint contracts are owned
by the sibling sub-skills.

## `LitAPI` constructor

Prefer configuring request behavior on the API object:

```python
api = MyAPI(
    max_batch_size=1,
    batch_timeout=0.0,
    api_path="/predict",
    stream=False,
    loop="auto",
    spec=None,
    mcp=None,
    enable_async=False,
)
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `max_batch_size` | `1` | Maximum number of requests to batch together. Must be greater than zero. |
| `batch_timeout` | `0.0` | Seconds to wait for a batch to fill. Must be non-negative and no larger than `LitServer(timeout=...)` unless timeout is disabled. |
| `api_path` | `"/predict"` | POST route for this API. Must start with `/` and must not collide with sibling APIs or reserved internal paths. |
| `stream` | `False` | Use streaming response handling. `predict()` and `encode_response()` should yield items. |
| `loop` | `"auto"` | LitServe loop selection. Use `"auto"` unless supplying a custom `LitLoop`. |
| `spec` | `None` | API spec adapter. Route OpenAI chat/embedding work to `openai-specs`. |
| `mcp` | `None` | MCP connector. Route MCP work to `mcp`. |
| `enable_async` | `False` | Requires async-compatible methods. `predict` must be async when enabled. |

Validation facts:

- `max_batch_size <= 0` raises `ValueError`.
- `batch_timeout < 0` raises `ValueError`.
- `api_path` without a leading `/` raises `ValueError`.
- A string `loop` must be `"auto"`; otherwise pass an actual loop object.
- If `enable_async=True`, `predict` must be an async function or async generator.
  Sync `decode_request` and `encode_response` are warned about and asyncified; sync
  `predict` is an error.

## `LitAPI` methods to implement

A minimal API implements `setup` and `predict`. Override decode/encode hooks when the
HTTP body and model input/output do not already match.

```python
class MyAPI(ls.LitAPI):
    def setup(self, device):
        self.model = load_model(device)

    def decode_request(self, request):
        return request["input"]

    def predict(self, x):
        return self.model(x)

    def encode_response(self, output):
        return {"output": output}
```

| Method | Called where | Contract |
| --- | --- | --- |
| `setup(self, device)` | Worker process startup | Load model/resources once per worker. `device` is usually `"cpu"`, `"cuda:0"`, `"mps:0"`, or a list for grouped devices. |
| `decode_request(self, request, **kwargs)` | API server process before queuing work | Convert FastAPI/Pydantic/JSON/form data into a picklable model input. |
| `predict(self, x, **kwargs)` | Inference worker | Run inference. For batching, receives a batched input and should return one output per request. For streaming, yield items. |
| `encode_response(self, output, **kwargs)` | Inference worker and response path | Convert model output to HTTP response data. For streaming, yield response chunks. |
| `batch(self, inputs)` | Batched loop before `predict` | Convert a list of per-request inputs to a model batch. Default stacks Torch tensors, stacks NumPy arrays, otherwise returns the list. |
| `unbatch(self, output)` | Batched loop after `predict` | Convert batched output to a list of per-request outputs. Default becomes available after server setup; implement it for non-list outputs. |
| `format_encoded_response(self, data)` | Streaming formatting helper | Dicts and Pydantic models become newline-delimited JSON strings; other objects are returned unchanged. |
| `health(self)` | `GET /health` | Return `True` when the API-specific health check passes. May be sync or async. |
| `authorize(self, ...)` | Endpoint dependency, if defined | Optional custom FastAPI dependency. Raise `HTTPException(401, ...)` on rejection. |
| `log(self, key, value)` | Any API method | Enqueue a key/value log event for configured `Logger` instances; warns if no logger is configured. |

### Context injection

LitServe can inject a per-request `context` dictionary when a hook declares a parameter
named exactly `context`. This is useful for carrying request metadata through batching,
prediction, unbatching, and encoding. In batched hooks, `context` is a list aligned with
inputs/outputs.

```python
def predict(self, x, context):
    context["raw_input"] = x
    return self.model(x)

def encode_response(self, output, context):
    return {"input": context["raw_input"], "output": output}
```

## Batching rules

Use batching when requests can be combined safely:

```python
api = MyAPI(max_batch_size=8, batch_timeout=0.05)
server = ls.LitServer(api, accelerator="cuda", devices=1)
```

Key rules:

- `predict` receives the result of `batch(inputs)`.
- Return one output per request, then let `unbatch` split it.
- If returning dictionaries, return a list of dictionaries, not a dictionary of lists.
- If implementing custom `batch`, implement matching `unbatch` unless the default list
  split is correct.
- `batch_timeout` must be smaller than `LitServer(timeout=...)` unless server timeout is
  disabled with `False` or `-1`.

## Streaming rules

Enable streaming on `LitAPI`, not `LitServer`:

```python
class TokenAPI(ls.LitAPI):
    def predict(self, prompt):
        for token in generate_tokens(prompt):
            yield token

    def encode_response(self, output_stream):
        for token in output_stream:
            yield {"token": token}

api = TokenAPI(stream=True)
server = ls.LitServer(api)
```

For batched streaming, each `encode_response` yield should provide one per-request
payload per active request for that stream step. Disable gzip for streaming responses is
handled by LitServe automatically.

## `LitServer` constructor

```python
server = ls.LitServer(
    lit_api,
    accelerator="auto",
    devices="auto",
    workers_per_device=1,
    timeout=30,
    healthcheck_path="/health",
    info_path="/info",
    shutdown_path="/shutdown",
    enable_shutdown_api=False,
    model_metadata=None,
    spec=None,
    max_payload_size=None,
    track_requests=False,
    callbacks=None,
    middlewares=None,
    loggers=None,
    fast_queue=False,
    disable_openapi_url=False,
    restart_workers=False,
)
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `lit_api` | required | One `LitAPI` or a non-empty iterable of `LitAPI` objects. |
| `accelerator` | `"auto"` | `"auto"`, `"cpu"`, `"cuda"`, or `"mps"`. `"gpu"` is accepted by the connector but explicit backends are clearer. |
| `devices` | `"auto"` | Device count or device id list for GPU/MPS. CPU resolves to one CPU device. |
| `workers_per_device` | `1` | Integer for all APIs, list/tuple matching APIs, or mapping `{api_path: workers}`. Values must be integers `>= 1`. |
| `timeout` | `30` | Request timeout seconds. Use `False` or `-1` to disable timeouts. |
| `healthcheck_path` | `"/health"` | Health endpoint. Must start with `/`. |
| `info_path` | `"/info"` | Info endpoint. Must start with `/`. |
| `shutdown_path` | `"/shutdown"` | Shutdown endpoint path when enabled. Must start with `/`. |
| `enable_shutdown_api` | `False` | Adds `POST /shutdown` protected by `LIT_SHUTDOWN_API_KEY` bearer token. |
| `model_metadata` | `None` | JSON-serializable metadata returned by `/info`. |
| `max_payload_size` | `None` | Adds a payload-size middleware; over-limit requests return `413`. |
| `track_requests` | `False` | Tracks active request counts for callbacks and request-count middleware. |
| `callbacks` | `None` | One `Callback` or a list of callbacks. |
| `middlewares` | `None` | List of middleware callables or `(MiddlewareClass, kwargs)` tuples. A single tuple is invalid. |
| `loggers` | `None` | One `Logger` or a list of logger instances. |
| `fast_queue` | `False` | Use ZeroMQ transport for high-throughput scenarios; disabled on Windows. |
| `disable_openapi_url` | `False` | Disable `/openapi.json`; `/docs` depends on OpenAPI being enabled. |
| `restart_workers` | `False` | Restart failed inference workers instead of shutting down. |

Deprecated compatibility arguments on `LitServer` are `max_batch_size`,
`batch_timeout`, `stream`, `api_path`, `loop`, and `spec`. Move them to `LitAPI`.

## `LitServer.run`

```python
server.run(
    host="0.0.0.0",
    port=8000,
    num_api_servers=None,
    log_level="info",
    generate_client_file=True,
    api_server_worker_type="process",
    pretty_logs=False,
    **uvicorn_kwargs,
)
```

Validation and behavior:

- `port` is cast to `int` and must be `1024 <= port <= 65535`.
- `host` must be exactly `"0.0.0.0"`, `"127.0.0.1"`, or `"::"`.
- `num_api_servers=None` uses the total inference-worker count.
- `num_api_servers < 1` raises `ValueError`.
- `api_server_worker_type` is `"process"` or `"thread"`; Windows uses threads.
- `pretty_logs=True` uses richer formatting when the `rich` package is available.
- Additional keyword arguments are passed into uvicorn; SSL options can also be supplied
  through uvicorn kwargs or environment-supported SSL context handling.
- `generate_client_file=True` writes `client.py` in the current working directory if it
  does not already exist.

## Built-in endpoints

| Endpoint | Method | Response |
| --- | --- | --- |
| `/` | `GET` | Plain text `litserve running`. |
| API path, default `/predict` | `POST` | Result of `encode_response`. |
| `healthcheck_path`, default `/health` | `GET` | `200 ok` only when workers are ready and every API `health()` returns true; otherwise `503 not ready`. |
| `info_path`, default `/info` | `GET` | JSON with `model_metadata`, `devices`, `workers_per_device`, `timeout`, per-route stream flags, `max_payload_size`, and `track_requests`. |
| `/docs` | `GET` | FastAPI Swagger UI unless OpenAPI is disabled. |
| `/openapi.json` | `GET` | OpenAPI schema unless disabled. |
| `shutdown_path`, default `/shutdown` | `POST` | Graceful shutdown trigger when `enable_shutdown_api=True`. |

## Authentication

### Per-API custom auth

Define `authorize` on a `LitAPI` when each endpoint needs its own dependency:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

class AuthedAPI(ls.LitAPI):
    def authorize(self, auth: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        if auth.scheme != "Bearer" or auth.credentials != "expected-token":
            raise HTTPException(status_code=401, detail="Bad token")
```

For multi-endpoint servers, each API's own `authorize` method is enforced on its route.

### Global API key

If the environment variable `LIT_SERVER_API_KEY` is set, LitServe requires clients to
send `X-API-Key: <value>` unless a route has a custom `authorize` method.

### Shutdown API key

When `enable_shutdown_api=True`, `POST /shutdown` uses
`Authorization: Bearer <LIT_SHUTDOWN_API_KEY>`. If the environment variable is missing,
LitServe generates a one-time token and logs it; production deployments should set the
variable explicitly.

## Callbacks

Subclass `litserve.Callback` and pass `callbacks=[...]` or a single callback instance.
Available hook names are:

- `on_before_setup`, `on_after_setup`
- `on_before_decode_request`, `on_after_decode_request`
- `on_before_predict`, `on_after_predict`
- `on_before_encode_response`, `on_after_encode_response`
- `on_server_start`, `on_server_end`
- `on_request`, `on_response`

Bundled default callbacks include:

```python
from litserve.callbacks.defaults import PredictionTimeLogger
from litserve.callbacks.defaults.metric_callback import RequestTracker

server = ls.LitServer(api, callbacks=[PredictionTimeLogger(), RequestTracker()], track_requests=True)
```

`RequestTracker` logs `Active requests: <count>`; without `track_requests=True`, the
active count is `None`. Callback exceptions are logged and do not stop other callbacks.

## Loggers

Subclass `litserve.Logger` and pass logger instances to `LitServer`. From inside a
`LitAPI`, call `self.log(key, value)`.

```python
class PrintLogger(ls.Logger):
    def process(self, key, value):
        print(key, value)

class API(ls.LitAPI):
    def predict(self, x):
        self.log("input", x)
        return x

server = ls.LitServer(API(), loggers=PrintLogger())
```

`Logger.mount(path, app)` can mount an ASGI app, for example a `/metrics` endpoint.
Logger instances should be pickleable; non-pickleable loggers may be recreated by class
in the logger process.

## Middleware

Use a list. Each entry may be a middleware class/callable or a tuple of
`(MiddlewareClass, kwargs)`:

```python
from starlette.middleware.trustedhost import TrustedHostMiddleware

server = ls.LitServer(
    api,
    middlewares=[
        (TrustedHostMiddleware, {"allowed_hosts": ["localhost", "127.0.0.1"]}),
    ],
    max_payload_size=10 * 1024 * 1024,
)
```

LitServe adds `GZipMiddleware` automatically for non-streaming APIs. It adds
`MaxSizeMiddleware` when `max_payload_size` is not `None`. `track_requests=True` adds
request-count middleware to each app copy used by API-server workers.

## Multiple endpoints

Pass a list of API objects with unique paths:

```python
sentiment = SentimentAPI(api_path="/sentiment")
generate = GenerateAPI(api_path="/generate")
server = ls.LitServer([sentiment, generate], workers_per_device={"/sentiment": 1, "/generate": 2})
```

Rules:

- The iterable cannot be empty.
- Paths must be unique.
- `/health` and `/info` are reserved by LitServe internals.
- `workers_per_device` mapping keys must match known API paths.
- Mixed streaming and non-streaming APIs are supported by the response buffer logic, but
  design client handling carefully because streaming and regular routes behave differently.

## Client generation

`server.run(generate_client_file=True)` calls `LitServer.generate_client_file(port)`.
It writes a simple `client.py` in the current working directory only if that file does not
already exist. Use `generate_client_file=False` in production entrypoints when the working
directory should not be mutated.

## Docker and deployment wrappers

The package CLI exposes:

```bash
litserve dockerize server.py --port 8000
litserve dockerize server.py --port 8000 --gpu
```

Behavior:

- The server file must exist in the current directory.
- A `Dockerfile` is written in the current directory.
- If `requirements.txt` exists, the Dockerfile installs it with LitServe.
- If `requirements.txt` is absent, a warning reminds you to edit dependencies manually.
- CPU Dockerfiles use a `python:$PYTHON_VERSION-slim` base.
- GPU Dockerfiles use an NVIDIA CUDA Ubuntu base and require a GPU-capable container runtime.

The `lightning` entry point is a passthrough to the Lightning SDK CLI. If
`lightning_sdk` is missing, it tries to install `lightning-sdk` using pip first, then uv.
If both fail, install `lightning-sdk` manually and rerun the deployment command.
