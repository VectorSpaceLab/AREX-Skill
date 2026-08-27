# Service Authoring API Reference

This reference captures the current BentoML SDK facts needed to author services without consulting source docs.

## Decorator Signatures

```python
bentoml.service(
    inner=None,
    *,
    name=None,
    image=None,
    description=None,
    path_prefix=None,
    envs=None,
    labels=None,
    cmd=None,
    service_class=Service,
    **kwargs,
)
```

`@bentoml.service` marks a class as a service. `**kwargs` are service config values such as `resources`, `workers`, `traffic`, `metrics`, `logging`, and related server settings. The returned service object is what BentoML loads, serves, and converts to ASGI.

```python
bentoml.api(
    func=None,
    *,
    route=None,
    name=None,
    input_spec=None,
    output_spec=None,
    batchable=False,
    batch_dim=0,
    max_batch_size=100,
    max_latency_ms=60000,
)
```

`@bentoml.api` exposes a method as an inference API. Methods whose names start with `__` are invalid API methods. If `route` is omitted, BentoML derives the route from the method. Use `name` when the public API name should differ from the Python method name.

```python
bentoml.task(
    func=None,
    *,
    route=None,
    name=None,
    input_spec=None,
    output_spec=None,
    batchable=False,
    batch_dim=0,
    max_batch_size=100,
    max_latency_ms=60000,
)
```

`@bentoml.task` uses the same schema and batching parameters as `@bentoml.api`, but marks the endpoint as an async task queue endpoint. A task endpoint cannot return a stream.

```python
bentoml.asgi_app(app, *, path="/", name=None)
bentoml.gradio.mount_gradio_app(blocks, path="/ui", name="gradio_ui")
bentoml.depends(ServiceClass, *, deployment=None, cluster=None, url=None)
```

Use `asgi_app` for FastAPI, Starlette, Quart, and WebSocket routes. Use Gradio mounting for UI surfaces. Use `depends` to compose services locally or across deployments.

## Service Class Fields

A decorated service object records:

- `name`: explicit `name=` or the class name.
- `config`: service config kwargs.
- `image`: optional `bentoml.images.Image` instance.
- `description`, `path_prefix`, `envs`, `labels`, and optional `cmd`.
- `apis`: methods decorated with `@bentoml.api` or `@bentoml.task`.
- `dependencies`: class attributes declared with `bentoml.depends(...)`.
- `mount_apps`: apps mounted through `@bentoml.asgi_app` or Gradio.

The service import string must resolve to a module-level service object. Avoid defining the service interactively or only inside `if __name__ == "__main__"`.

## IO Schemas

Prefer type hints first. BentoML infers schemas for common Python, Pydantic, and ML types:

- Standard JSON-like types: `str`, `int`, `float`, `bool`, `list`, `dict`.
- Structured payloads: `pydantic.BaseModel`, or `@bentoml.api(input_spec=MyModel)` to pass validated fields as `**kwargs`.
- File payloads: `pathlib.Path`; restrict media types with `typing.Annotated[Path, bentoml.validators.ContentType("...")]`.
- Bytes payloads: `bytes` with `ContentType` metadata when a custom content type matters.
- Tensors and arrays: `numpy.ndarray`, `torch.Tensor`, `tensorflow.Tensor` with `Shape(...)` and `DType(...)` validators.
- Tables: `pandas.DataFrame` with `DataframeSchema(...)` metadata.
- Images: `PIL.Image.Image` or file `Path` with image content type.
- Root input: a single positional-only argument receives the raw payload instead of an object keyed by argument name.

When inference fails, provide explicit `input_spec=` and `output_spec=` subclasses of `bentoml.IODescriptor` or Pydantic models.

## Batching

Set `batchable=True` only when the method accepts and returns batched values. A batchable endpoint:

- Accepts one batchable parameter, plus optional `bentoml.Context`.
- Should use a container or tensor that can hold multiple requests, such as `list[str]` or `numpy.ndarray`.
- Returns results aligned to the incoming batch boundaries.
- Uses `max_batch_size` to cap batch size and `max_latency_ms` to cap queueing latency.
- Uses `batch_dim=(input_dim, output_dim)` when input batching and output splitting occur along different axes.

For APIs with multiple logical inputs, define a Pydantic model or dataclass-like schema for one request and batch a `list[Model]`. If a synchronous wrapper service calls a batchable downstream service, increase service concurrency/threads where appropriate so enough calls can accumulate.

## Runtime Environment Hints

Use service-level hints for the service's own runtime needs:

```python
image = bentoml.images.Image(python_version="3.11").python_packages("torch", "transformers")

@bentoml.service(
    image=image,
    envs=[{"name": "HF_TOKEN"}],
    resources={"gpu": 1},
    workers=1,
)
class Inference:
    ...
```

`Image` supports `python_packages`, `requirements_file`, `pyproject_toml`, `system_packages`, `run`, `run_script`, and `build_include`. Keep detailed build/container decisions in the packaging sub-skill.

## Lifecycle Hooks And Context

- `@bentoml.on_deployment`: global setup before workers spawn; no `self` argument.
- `@bentoml.on_startup`: per-worker setup; may be sync or async and receives `self`.
- `@bentoml.on_shutdown`: cleanup; may be sync or async and receives `self`.
- `__is_alive__` and `__is_ready__`: return booleans for `/livez` and `/readyz`.
- `bentoml.Context`: add an API parameter to inspect request metadata, set response headers/status/cookies, use per-request temp dirs, or store per-worker state.

## ASGI, Gradio, WebSocket, Streaming

Mount ASGI apps with `@bentoml.asgi_app(app, path="/prefix")`. If the service has `path_prefix="/v1"`, the mounted app path is also prefixed. FastAPI routes can be declared inside the service class and use `self`, or outside and use `bentoml.get_current_service()`.

Mount Gradio with `@bentoml.gradio.mount_gradio_app(interface_or_blocks, path="/ui")`. Ensure the generated runtime image or local environment includes `fastapi` and `gradio`.

For WebSockets, mount a FastAPI app and define `@app.websocket("/ws")`. The BentoML Python HTTP clients do not support WebSocket endpoints.

For streaming, return `typing.Generator` or `typing.AsyncGenerator` from an `@bentoml.api`. Do not use streaming returns with `@bentoml.task`.
