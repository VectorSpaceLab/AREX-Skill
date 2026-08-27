---
name: service-authoring
description: "Author BentoML services and APIs with the current class-based SDK,
  including service decorators, API/task endpoints, IO specs, batching,
  dependencies, lifecycle hooks, ASGI/Gradio/WebSocket/streaming integrations,
  GPU/runtime hints, and service-loading checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BentoML Service Authoring

Use this sub-skill when creating or debugging `service.py` and other BentoML service modules. It focuses on Python SDK authoring, not Bento packaging, model-store import mechanics, client usage, observability, cloud deployment, or CLI operations.

## Route The Work

- For service class structure, endpoint decorators, IO annotations, batching, service dependencies, hooks, ASGI/Gradio/WebSocket/streaming, and local import checks, stay here.
- For `bentoml build`, Bento image/container settings, `bentofile.yaml`, include/exclude rules, or containerization, use `../packaging-and-containerization/SKILL.md`.
- For `bentoml serve`, `SyncHTTPClient`, `AsyncHTTPClient`, HTTP calls, and server flags, use `../serving-and-clients/SKILL.md`.
- For framework-specific model saving/loading, Model Store tags, and import APIs, use `../model-management/SKILL.md`.
- For metrics, tracing, logging, scaling, config overrides, and operations, use `../observability-and-operations/SKILL.md`.
- For `bentoml deploy`, BentoCloud resources, secrets, and deployment config, use `../cli-and-cloud/SKILL.md`.

## Authoring Checklist

1. Put the service in an importable module, usually `service.py`, and assign the decorated class at module scope.
2. Decorate a class with `@bentoml.service` or `@bentoml.service(...)`; default service name is the class name.
3. Keep heavyweight framework imports in `__init__`, lifecycle hooks, or `with bentoml.importing():` if they may be absent during tooling/import-only phases.
4. Define public endpoints with `@bentoml.api` or `@bentoml.api(...)`; use `@bentoml.task` only for asynchronous task-queue endpoints.
5. Add precise type hints or explicit `input_spec=` / `output_spec=` so BentoML can infer request/response schemas.
6. Validate importability before serving or building with `scripts/validate_service_target.py --target service:MyService --working-dir .`.

## Minimal Pattern

```python
from __future__ import annotations

import bentoml


@bentoml.service(name="text_tools", path_prefix="/v1")
class TextTools:
    @bentoml.api(route="/echo", name="echo")
    def echo(self, text: str) -> str:
        return text

    @bentoml.api(batchable=True, max_batch_size=32, max_latency_ms=1000)
    def summarize(self, texts: list[str]) -> list[str]:
        return [text[:80] for text in texts]
```

Generate a fuller starter service with:

```bash
python skills/bentoml/sub-skills/service-authoring/scripts/create_minimal_service.py --output service.py --class-name TextTools
```

## Key Decisions

- `@bentoml.service(...)` accepts `name`, `image`, `description`, `path_prefix`, `envs`, `labels`, `cmd`, `service_class`, and service config kwargs such as `resources`, `workers`, `traffic`, `metrics`, and `logging`.
- `path_prefix="/v1"` applies to BentoML API routes, mounted ASGI apps, and health endpoints such as `/v1/livez` and `/v1/readyz`.
- `@bentoml.api(...)` and `@bentoml.task(...)` share `route`, `name`, `input_spec`, `output_spec`, `batchable`, `batch_dim`, `max_batch_size`, and `max_latency_ms`; task endpoints must not return a stream.
- For batchable APIs, accept one batched argument plus optional `bentoml.Context`, return the matching batched structure, and set `batch_dim=(input_dim, output_dim)` when input and output split axes differ.
- Use `bentoml.depends(OtherService)` for service composition; call blocking dependency APIs through `.to_async` from async endpoints.
- Use `bentoml.images.Image(...).python_packages(...)` and `envs=[...]` as service-level runtime hints, but route full packaging decisions to packaging guidance.

## Advanced Integrations

- Lifecycle: use `@bentoml.on_deployment` for once-before-workers setup, `@bentoml.on_startup` for per-worker startup, `@bentoml.on_shutdown` for cleanup, and `__is_alive__` / `__is_ready__` for health checks.
- ASGI: create a FastAPI/Starlette/Quart app, mount it with `@bentoml.asgi_app(app, path="/app")`, and use `bentoml.get_current_service()` or class-route `self` to access service state.
- Gradio: create a Gradio `Interface`/`Blocks` and mount with `@bentoml.gradio.mount_gradio_app(blocks, path="/ui")`; include `fastapi` and `gradio` in the runtime environment.
- WebSocket: mount a FastAPI app with `@app.websocket(...)`; BentoML Python clients do not handle WebSocket endpoints, so author a direct WebSocket client for tests or consumers.
- Streaming: return a `Generator[...]` or `AsyncGenerator[...]` from `@bentoml.api`; BentoML defaults stream media type to `text/event-stream` when no explicit media type is inferred.
- GPU/runtime hints: put `resources={"gpu": 1}` or `resources={"gpu": 2}` on the service and select framework devices in `__init__`; use `bentoml.server_context.worker_index` when mapping multiple workers to devices.

## References

- `references/api-reference.md` for decorator signatures, route/schema choices, IO validators, and lifecycle/API patterns.
- `references/workflows.md` for common recipes: minimal services, batching, tasks, composition, ASGI/Gradio/WebSocket/streaming, and validation loops.
- `references/troubleshooting.md` for import target errors, missing runtime dependencies, invalid specs, batching mismatch, optional dependency gaps, service init side effects, and async task misuse.
- `scripts/create_minimal_service.py` to generate a safe starter service without relying on repository examples.
- `scripts/validate_service_target.py` to import a user service target from a chosen working directory and inspect APIs/tasks/routes without serving it.
