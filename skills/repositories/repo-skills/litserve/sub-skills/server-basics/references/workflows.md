# LitServe server workflows

These recipes assume LitServe is installed in the active Python environment.
Use the bundled scripts as starting points; copy them into your application directory
before editing for a real model.

## 1. Serve a minimal model

Use the bundled square server:

```bash
python scripts/minimal_server.py --host 127.0.0.1 --port 8000
```

Send a request from another terminal:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"input": 4.0}'
```

Expected response shape:

```json
{"output": 16.0, "device": "cpu"}
```

For a different port:

```bash
python scripts/minimal_server.py --port 8080
curl -X POST http://127.0.0.1:8080/predict -H "Content-Type: application/json" -d '{"input": 5}'
```

## 2. Adapt the minimal server to a real model

Pattern:

```python
import litserve as ls

class MyModelAPI(ls.LitAPI):
    def setup(self, device):
        # Load once per worker. Use `device` when your model supports it.
        self.model = load_model(device)

    def decode_request(self, request):
        # JSON body has already been parsed to a dict for normal requests.
        return request["input"]

    def predict(self, x):
        return self.model(x)

    def encode_response(self, output):
        return {"output": output}

if __name__ == "__main__":
    server = ls.LitServer(MyModelAPI(api_path="/predict"), accelerator="auto")
    server.run(host="127.0.0.1", port=8000)
```

Guidelines:

- Keep expensive model loading in `setup(device)`, not `__init__`.
- Keep request parsing in `decode_request` so `predict` can focus on model logic.
- Return JSON-serializable dictionaries or Pydantic models from `encode_response`.
- Use `host="127.0.0.1"` for local-only development and `host="0.0.0.0"` for Docker or remote access.

## 3. Choose accelerator, devices, workers, and API servers

CPU-only local development:

```python
server = ls.LitServer(api, accelerator="cpu", devices=1, workers_per_device=1)
```

Auto backend selection:

```python
server = ls.LitServer(api, accelerator="auto", devices="auto")
```

GPU/MPS examples:

```python
server = ls.LitServer(api, accelerator="cuda", devices=1)
server = ls.LitServer(api, accelerator="cuda", devices=[0, 1], workers_per_device=1)
server = ls.LitServer(api, accelerator="mps", devices=1)
```

HTTP server worker tuning:

```python
server.run(num_api_servers=4, api_server_worker_type="process")
```

Notes:

- `num_api_servers=None` uses the total number of inference workers.
- Increase `workers_per_device` for more parallel inference workers if the model fits in memory.
- Increase `num_api_servers` for HTTP throughput, not for model memory throughput.
- On Windows, API-server workers use threads.
- Use `fast_queue=True` for very high request rates when ZeroMQ is available; it is disabled on Windows.

## 4. Batch requests

Create the API with `max_batch_size > 1` and a small `batch_timeout`:

```python
class BatchAPI(ls.LitAPI):
    def decode_request(self, request):
        return float(request["input"])

    def predict(self, batch):
        # Default batch() returns a list for scalar inputs.
        return [x * x for x in batch]

    def encode_response(self, output):
        return {"output": output}

api = BatchAPI(max_batch_size=8, batch_timeout=0.05)
server = ls.LitServer(api, timeout=30)
```

If your model expects arrays/tensors, override both `batch` and `unbatch`:

```python
class ArrayBatchAPI(BatchAPI):
    def batch(self, inputs):
        import numpy as np
        return np.asarray(inputs, dtype="float32")

    def predict(self, batch):
        return batch * batch

    def unbatch(self, output):
        return output.tolist()
```

Batching checklist:

- Test with concurrent client requests; sequential requests may never share a batch.
- Ensure one output per input.
- Return a list of dictionaries for batched dictionary output.
- Keep `batch_timeout < timeout`, unless `timeout` is `False` or `-1`.

The bundled minimal server can be run in batch mode:

```bash
python scripts/minimal_server.py --max-batch-size 4 --batch-timeout 0.05 --port 8000
```

## 5. Stream responses

Use `stream=True` on `LitAPI` and yield from `predict` and `encode_response`:

```python
class StreamAPI(ls.LitAPI):
    def decode_request(self, request):
        return request["prompt"]

    def predict(self, prompt):
        for token in prompt.split():
            yield token

    def encode_response(self, output_stream):
        for token in output_stream:
            yield {"token": token}

api = StreamAPI(stream=True)
server = ls.LitServer(api)
```

Call with curl without buffering:

```bash
curl -N -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"prompt": "hello litserve"}'
```

Streaming notes:

- Dict and Pydantic chunks are newline-delimited JSON after formatting.
- Do not rely on gzip for streaming; LitServe avoids adding gzip middleware for streaming APIs.
- For OpenAI streaming protocols, route to `openai-specs` rather than hand-rolling the OpenAI schema here.

## 6. Use async handlers

Use `enable_async=True` only when `predict` is async:

```python
class AsyncAPI(ls.LitAPI):
    async def decode_request(self, request):
        return request["input"]

    async def predict(self, x):
        await call_external_service(x)
        return x * x

    async def encode_response(self, output):
        return {"output": output}

api = AsyncAPI(enable_async=True)
server = ls.LitServer(api)
```

Async validation rules:

- `predict` must be an async coroutine or async generator.
- `decode_request` and `encode_response` should also be async. If they are sync, LitServe warns and asyncifies them.
- Async is most useful for I/O-bound work such as database calls, HTTP clients, and storage APIs.

## 7. Serve file uploads and form data

Run the bundled file/form server:

```bash
python scripts/file_upload_server.py --host 127.0.0.1 --port 8000 --max-payload-size 10485760
```

Multipart upload:

```bash
printf 'hello litserve' > sample.txt
curl -X POST http://127.0.0.1:8000/predict -F 'input=@sample.txt'
```

URL-encoded form data:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'input=hello+form'
```

Implementation pattern:

```python
from fastapi import Request

class FileAPI(ls.LitAPI):
    def decode_request(self, request: Request):
        item = request["input"]
        if hasattr(item, "file"):
            data = item.file.read()
        else:
            data = str(item).encode("utf-8")
        return {"size": len(data), "text": data.decode("utf-8", errors="replace")}
```

File/form notes:

- Install `python-multipart` when serving multipart or form uploads.
- Decode uploaded files in `decode_request`; pass plain, picklable values into `predict`.
- Use `max_payload_size` to reject oversized uploads with HTTP `413`.

## 8. Serve base64 image payloads

Run the bundled image server:

```bash
python scripts/image_roundtrip_server.py --host 127.0.0.1 --port 8000 --transform invert
```

Generate a small payload and call it:

```bash
python scripts/image_roundtrip_server.py --print-sample-json > payload.json
curl -X POST http://127.0.0.1:8000/predict \
  -H 'Content-Type: application/json' \
  --data-binary @payload.json > response.json
```

Implementation pattern:

```python
from litserve.schema.image import ImageInput, ImageOutput

class ImageAPI(ls.LitAPI):
    def decode_request(self, request: ImageInput):
        return request.get_image().convert("RGB")

    def predict(self, image):
        return image

    def encode_response(self, image) -> ImageOutput:
        return ImageOutput(image=image)
```

Image notes:

- `ImageInput` expects base64 strings and raises validation errors for invalid base64.
- `ImageInput.get_image()` requires Pillow.
- `ImageOutput` serializes a PIL image to a PNG base64 string under the `image` field.

## 9. Add authentication

### Global API key

Set the environment variable before server startup:

```bash
export LIT_SERVER_API_KEY='dev-secret'
python scripts/minimal_server.py --port 8000
curl -X POST http://127.0.0.1:8000/predict \
  -H 'X-API-Key: dev-secret' \
  -H 'Content-Type: application/json' \
  -d '{"input": 4}'
```

### Per-route bearer token

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

class ProtectedAPI(ls.LitAPI):
    def authorize(self, auth: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        if auth.scheme != "Bearer" or auth.credentials != "alpha":
            raise HTTPException(status_code=401, detail="Bad token")
```

In a multi-endpoint server, each API can use a different `authorize` method or no auth.

### Shutdown endpoint

```bash
export LIT_SHUTDOWN_API_KEY='shutdown-secret'
```

```python
server = ls.LitServer(api, enable_shutdown_api=True)
```

Then call:

```bash
curl -X POST http://127.0.0.1:8000/shutdown \
  -H 'Authorization: Bearer shutdown-secret'
```

## 10. Add callbacks, request tracking, and loggers

Prediction time logging:

```python
from litserve.callbacks.defaults import PredictionTimeLogger
from litserve.callbacks.defaults.metric_callback import RequestTracker

server = ls.LitServer(
    api,
    callbacks=[PredictionTimeLogger(), RequestTracker()],
    track_requests=True,
)
```

Custom logger:

```python
class PrintLogger(ls.Logger):
    def process(self, key, value):
        print(f"{key}={value}")

class API(ls.LitAPI):
    def predict(self, x):
        self.log("input", x)
        return x

server = ls.LitServer(API(), loggers=PrintLogger())
```

Mount a metrics app:

```python
logger = PrintLogger()
logger.mount("/metrics", metrics_asgi_app)
server = ls.LitServer(api, loggers=logger)
```

## 11. Add middleware and payload limits

Trusted host middleware:

```python
from starlette.middleware.trustedhost import TrustedHostMiddleware

server = ls.LitServer(
    api,
    middlewares=[(TrustedHostMiddleware, {"allowed_hosts": ["localhost", "127.0.0.1"]})],
)
```

Custom response header middleware:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, length: int):
        super().__init__(app)
        self.length = length

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Request-Id"] = "0" * self.length
        return response

server = ls.LitServer(api, middlewares=[(RequestIdMiddleware, {"length": 8})])
```

Payload-size limit:

```python
server = ls.LitServer(api, max_payload_size=25 * 1024 * 1024)
```

## 12. Expose multiple endpoints

```python
class NamedAPI(ls.LitAPI):
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.name = name

    def decode_request(self, request):
        return request["input"]

    def predict(self, x):
        return x * x

    def encode_response(self, output):
        return {"name": self.name, "output": output}

api1 = NamedAPI("api1", api_path="/api1")
api2 = NamedAPI("api2", api_path="/api2")
server = ls.LitServer([api1, api2], workers_per_device={"/api1": 1, "/api2": 2})
```

Call each path independently:

```bash
curl -X POST http://127.0.0.1:8000/api1 -H 'Content-Type: application/json' -d '{"input": 2}'
curl -X POST http://127.0.0.1:8000/api2 -H 'Content-Type: application/json' -d '{"input": 5}'
```

Avoid:

- Duplicate `api_path` values.
- `api_path="/health"` or `api_path="/info"`.
- `workers_per_device` mappings with unknown paths.

## 13. Generate `client.py`

During development, let `server.run` create a simple client:

```python
server.run(port=8123, generate_client_file=True)
```

It writes `client.py` in the current working directory if absent. If `client.py`
already exists, LitServe skips generation instead of overwriting it.

For scripts where filesystem mutation is undesirable, use:

```python
server.run(generate_client_file=False)
```

## 14. Generate a Dockerfile

Prepare an application directory with your server file and optional `requirements.txt`:

```bash
cp scripts/minimal_server.py server.py
printf 'litserve==0.2.18\n' > requirements.txt
litserve dockerize server.py --port 8000
```

For GPU image scaffolding:

```bash
litserve dockerize server.py --port 8000 --gpu
```

Then inspect and edit the generated `Dockerfile` for model weights, system packages,
extra Python dependencies, and secrets handling. Build and run:

```bash
docker build -t litserve-model .
docker run -p 8000:8000 litserve-model:latest
```

GPU containers require a compatible NVIDIA runtime:

```bash
docker run --gpus all -p 8000:8000 litserve-model:latest
```

## 15. Deploy with the Lightning CLI passthrough

The package installs a `lightning` entry point that delegates to the Lightning SDK CLI.
Typical commands are:

```bash
lightning deploy server.py --cloud
lightning deploy server.py
```

If the SDK is not installed, the wrapper tries to install `lightning-sdk` using pip,
then uv. If auto-install fails, run:

```bash
python -m pip install -U lightning-sdk
```

Then retry the Lightning command.

## 16. Check health, info, and shutdown

Health:

```bash
curl -i http://127.0.0.1:8000/health
```

`200 ok` means at least one worker is ready and every API's `health()` returned true.
`503 not ready` means workers are still starting, failed, or an API health check failed.

Info:

```bash
curl http://127.0.0.1:8000/info
```

The response includes model metadata and server configuration.

Shutdown, if enabled:

```bash
curl -X POST http://127.0.0.1:8000/shutdown \
  -H 'Authorization: Bearer <LIT_SHUTDOWN_API_KEY>'
```

## 17. Safe smoke pattern

A minimal smoke check should start the server in a subprocess, wait for `/health`, send
one `/predict` request, and then terminate the process tree. Keep the smoke small and
CPU-only. Do not use throughput, parity, Torch, CUDA, transformer, or vision benchmark
harnesses for server-basics verification; those paths were intentionally excluded from
this sub-skill.
