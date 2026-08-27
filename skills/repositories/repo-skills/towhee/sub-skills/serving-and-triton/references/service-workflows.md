# Towhee API service workflows

This reference covers service construction and command shapes. It assumes the
pipeline/function behavior has already been chosen elsewhere.

## API surface

| Surface | Shape | Use | Notes |
|---|---|---|---|
| `api_service.APIService` | `APIService(desc: str = "")` | Mutable service container for route registrations. | `routers` is `None` until the first route is added, then a list of route configs. |
| `APIService.api` | `service.api(input_model=None, output_model=None, path=None)` | Decorator that registers a callable and returns the original callable. | Always pass an explicit `path` such as `"/echo"`. |
| `APIService.add_api` | `service.add_api(func, input_model=None, output_model=None, path=None)` | Programmatic route registration. | Equivalent to the decorator after a callable already exists. |
| Route config | `func`, `input_model`, `output_model`, `path` | Stored route metadata consumed by HTTP/gRPC servers. | Input/output models are Towhee IO wrappers, not bare Pydantic models. |
| `api_service.build_service` | `build_service(pipelines, desc="Welcome to use towhee pipeline service")` | Convert one or more `(runtime_pipeline, path)` pairs into an `APIService`. | Adds the base path and, when the pipeline has `.batch`, `path + "/batch"`. |

Installed signature snapshot:

```python
APIService.api(self, input_model=None, output_model=None, path=None)
APIService.add_api(self, func, input_model=None, output_model=None, path=None)
api_service.build_service(pipelines, desc='Welcome to use towhee pipeline service')
```

## Direct Python service pattern

Use this when you need custom request/response schemas or custom functions.

```python
from pydantic import BaseModel
from towhee import api_service
from towhee.serve.io import JSON

class EchoRequest(BaseModel):
    text: str
    repeat: int = 1

class EchoResponse(BaseModel):
    text: str
    repeated: list[str]

service = api_service.APIService(desc="Example Towhee service")

@service.api(path="/echo", input_model=JSON(EchoRequest), output_model=JSON(EchoResponse))
def echo(item: EchoRequest) -> EchoResponse:
    return EchoResponse(text=item.text, repeated=[item.text] * item.repeat)
```

Key points:

- `JSON(Model)` wraps a Pydantic model for request parsing/response serialization.
- `JSON()`, `TEXT()`, `BYTES()`, and `NDARRAY()` are IO wrappers. Do not pass a
  raw Pydantic model as `input_model` or `output_model`.
- If no input/output model is supplied, HTTP defaults to `JSON()`. gRPC infers
  `BYTES`, `NDARRAY`, `TEXT`, or `JSON` from the protobuf content.
- The HTTP adapter inspects the callable signature:
  - zero parameters: calls `func()`;
  - one parameter: calls `func(values)`;
  - multiple parameters: calls `func(**values)` if decoded values are a dict,
    otherwise `func(*values)`.

## Build a service from RuntimePipeline objects

Use `build_service` when an existing Towhee runtime pipeline should be exposed
without hand-writing route functions.

```python
from towhee import api_service, pipe

p = (
    pipe.input("x")
        .map("x", "y", lambda x: x)
        .output("y")
)

service = api_service.build_service([(p, "/echo")], desc="Pipeline service")
```

Expected registration behavior:

- `"/echo"` calls the pipeline once. If the result has `to_list()`, it is
  converted before returning.
- `"/echo/batch"` is registered when the pipeline exposes `.batch`; it calls
  `pipeline.batch(params)` and converts per-item results that provide `to_list()`.
- Multiple pipelines are supplied as `[(pipeline_a, "/a"), (pipeline_b, "/b")]`.

## `towhee server` command shapes

The CLI supports two service sources: a Python module variable or Towhee hub
pipeline repositories. These shapes start live servers, so use them only for
explicit deployment/testing requests.

### Python module service

A Python file can expose a variable named `service` that is an `APIService`.
The command source is `<module>:<service_variable>`.

```bash
towhee server my_service:service --host 0.0.0.0 --http-port 40001
```

For gRPC, provide `--grpc-port`; the server chooses gRPC when this flag is set.

```bash
towhee server my_service:service --host 0.0.0.0 --grpc-port 50001
```

Operational details:

- The module name omits `.py`.
- The CLI inserts both the current working directory's module parent and the
  resolved file parent into `sys.path`, then imports the module attribute.
- If both `--http-port` and `--grpc-port` are supplied, gRPC wins because the CLI
  branches on presence of `--grpc-port`.

### Repository-based pipeline service

The repository mode loads one `AutoConfig` and one `AutoPipes.pipeline` per
source, then passes them to `build_service` with the supplied URIs.

```bash
towhee server audio-embedding image-embedding \
  --host 0.0.0.0 \
  --grpc-port 50001 \
  --uri /emb/audio /emb/image \
  --params none model_name=resnet34,device=0
```

Rules for repository mode:

- `source` entries and `--uri` entries must align positionally.
- `--params` entries also align positionally. Use `none` to leave that pipeline's
  loaded config unchanged.
- Parameter strings are comma-separated `key=value` pairs. Integer and floating
  values are converted from strings before updating the config object.
- Repository loading may involve hub/network/model behavior. Do not use it for a
  local smoke check when a direct `APIService` object is sufficient.

## Client expectations

### HTTP

HTTP routes are `POST` endpoints. JSON routes accept a JSON request body and
return JSON-compatible content.

```python
import requests

response = requests.post(
    "http://127.0.0.1:40001/echo",
    json={"text": "towhee", "repeat": 2},
    timeout=10,
)
response.raise_for_status()
print(response.json())
```

Use `data=` for raw text/bytes routes when the route's IO wrapper expects raw
body bytes instead of JSON decoding.

### gRPC

The sync gRPC client uses a route path and an optional IO model.

```python
from towhee.serve.grpc.client import Client

with Client(host="127.0.0.1", port=50001) as client:
    result = client("/echo", {"text": "towhee", "repeat": 2})
    assert result.code == 0
    print(result.content)
```

If `result.code != 0`, `content` is `None` and `msg` contains the server-side
error message. Unknown paths are reported as service errors.

## Safe service verification checklist

1. Import Towhee and construct the `APIService` object.
2. Assert that `service.routers` contains the expected paths.
3. Call the underlying route function directly with representative Python values.
4. If using `build_service`, assert base and batch paths are present.
5. Stop here for routine checks. Start HTTP/gRPC only when deployment behavior,
   port binding, or network clients are the explicit target.
