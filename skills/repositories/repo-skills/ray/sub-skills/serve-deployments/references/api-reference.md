# Ray Serve API and CLI Reference

This reference summarizes the Serve entry points most agents need when authoring, running, or debugging Ray Serve applications. It is distilled from the Ray Serve Python package, Serve CLI implementation, and Serve documentation.

## Install and imports

Install only the Serve extra unless the task needs another Ray library:

```bash
pip install "ray[serve]"
```

Typical imports:

```python
from ray import serve
from starlette.requests import Request
```

Ray supports Python 3.10+ in this repository generation context. A verified inspection environment imported `ray`, `ray.data`, `ray.train`, `ray.tune`, `ray.serve`, and `ray.rllib`; for Serve-specific work, do not require the unrelated extras.

## Core Python API

### `@serve.deployment`

Use `@serve.deployment` on a class or function to turn it into a Serve deployment. Common decorator options include:

| Option | Use |
| --- | --- |
| `name` | Override the deployment name used in configs and status. |
| `num_replicas` | Fixed replica count, or omit when autoscaling. |
| `route_prefix` | Legacy/decorator route setting; prefer app-level `route_prefix` in config or `serve.run`. |
| `ray_actor_options` | Per-replica Ray actor resources, such as `num_cpus`, `num_gpus`, `resources`, `memory`, `runtime_env`, `accelerator_type`, and label selectors. |
| `autoscaling_config` | Serve autoscaling settings; do not combine a fixed integer `num_replicas` with an autoscaling config. |
| `user_config` | JSON-serializable data passed to `reconfigure`; can be updated without restarting replicas. |
| `max_ongoing_requests` | Max concurrent requests per replica; keep it high enough for batching. |
| `max_queued_requests` | Backpressure limit at each caller/proxy; HTTP callers may see 503 when exceeded. |
| `graceful_shutdown_timeout_s` / `graceful_shutdown_wait_loop_s` | Replica shutdown timing. |
| `health_check_period_s` / `health_check_timeout_s` | Replica health check timing. |
| `logging_config` | Deployment-specific log config. |
| `request_router_config` | Request routing policy and stats options. |

Minimal class deployment:

```python
from typing import Dict
from starlette.requests import Request
from ray import serve

@serve.deployment(
    num_replicas=1,
    ray_actor_options={"num_cpus": 0.25},
)
class MyModel:
    def __init__(self, message: str = "ok"):
        self.message = message

    def __call__(self, request: Request) -> Dict[str, str]:
        return {"result": self.message}

app = MyModel.bind(message="hello")
```

### `Deployment.bind`

Call `.bind(...)` on deployment objects to build an application graph. The bound arguments become constructor/function arguments for the deployment. For composition, pass one bound deployment into another deployment's constructor:

```python
@serve.deployment
class Preprocessor:
    def __call__(self, text: str) -> str:
        return text.strip().lower()

@serve.deployment
class Model:
    def __init__(self, preprocessor):
        self.preprocessor = preprocessor

    async def __call__(self, request):
        payload = await request.json()
        cleaned = await self.preprocessor.__call__.remote(payload["text"])
        return {"cleaned": cleaned}

app = Model.bind(Preprocessor.bind())
```

### `serve.run`

`serve.run(target, blocking=False, name="default", route_prefix="/", logging_config=None, _local_testing_mode=False, external_scaler_enabled=False)` runs a bound Serve application and returns a handle to the ingress deployment. In a script, guard long-running behavior behind `if __name__ == "__main__"` so importing the module for `serve build` or tests does not start services.

```python
if __name__ == "__main__":
    serve.run(app, route_prefix="/predict")
```

### `serve.batch`

`serve.batch(max_batch_size=10, batch_wait_timeout_s=0.01, max_concurrent_batches=1)` converts an `async def` method/function to batched execution. If batching never fills, check that `max_ongoing_requests >= max_batch_size * max_concurrent_batches`.

```python
@serve.deployment(max_ongoing_requests=32)
class BatchedModel:
    @serve.batch(max_batch_size=8, batch_wait_timeout_s=0.05)
    async def classify(self, inputs: list[str]) -> list[str]:
        return [text.upper() for text in inputs]
```

## HTTP, FastAPI, and gRPC

- Plain Serve deployments receive Starlette `Request` objects by default when called over HTTP.
- Return JSON-serializable Python objects for simple JSON responses.
- Use FastAPI ingress when the service needs typed routes, request validation, multiple HTTP methods, or richer path parsing.
- HTTP proxy defaults in the installed API inspection were `host="127.0.0.1"`, `port=8000`, `location=HeadOnly`, request timeout optional, keep-alive timeout `90`, and optional TLS fields.
- Serve YAML production docs commonly expose HTTP with `host: 0.0.0.0` and `port: 8000`; choose `127.0.0.1` for local-only development.
- gRPC is configured through `grpc_options.port` and `grpc_options.grpc_servicer_functions`; if no servicer functions are configured, no user gRPC service is started.

## Serve CLI commands

The `serve` console script manages Serve applications on a Ray cluster.

| Command | Purpose | Notes |
| --- | --- | --- |
| `serve run module:app` | Develop/run an app from an import path. | Blocks by default and tears down Serve on `Ctrl-C`. |
| `serve run config.yaml` | Run apps from a config file locally/dev style. | Existing apps with no code changes are not updated. |
| `serve deploy module:app` | Submit a deploy request from an import path. | Requires a running Ray cluster dashboard API. |
| `serve deploy config.yaml` | Submit production-style app config. | Idempotent; cluster config converges to last successful config. |
| `serve build module:app -o serve_config.yaml` | Generate YAML from bound app code. | Generated `runtime_env` is empty; fill it manually. |
| `serve status` | Print application and deployment status. | Use `-n <app>` for one app. |
| `serve config` | Print currently deployed config. | Shows no config for apps created only through `serve.run`. |
| `serve start` | Start Serve on an existing Ray cluster. | Cluster lifecycle belongs to cluster operations. |
| `serve shutdown` | Delete Serve applications on the cluster. | Use cautiously; can prompt unless `--yes`. |
| `serve controller-health` | Inspect Serve controller health metrics. | Connects to a running Ray cluster. |

Common local development commands:

```bash
serve run app_module:app --app-dir . --route-prefix /predict
serve run app_module:app model_path=models/latest.pkl num_replicas=2
serve build app_module:app -o serve_config.yaml
```

Common production-style commands:

```bash
serve deploy serve_config.yaml
serve status
serve config
serve status -n default
serve config -n default
```

`serve deploy` prints that the request was sent; it does not guarantee replicas are already healthy. Follow with `serve status` until the application is `RUNNING` and deployments are `HEALTHY`.

## Application builder arguments

Both `serve run` and `serve deploy` can pass arguments after an import path when the import path points to a function that returns an application:

```bash
serve run app_factory:create_app model_path=/models/latest threshold=0.7
serve deploy app_factory:create_app model_path=s3://bucket/model.pkl
```

Arguments use `key=value` strings. Do not pass application arguments with a YAML config file; config mode carries arguments in the YAML `args` field.

## Development checklist

- Keep module import side effects small; importing `module:app` should not start model downloads, `serve.run`, or HTTP clients unexpectedly.
- Define the bound `app` at module scope for `serve run module:app` and `serve build module:app`.
- Use `ray_actor_options` for replica CPU/GPU/custom-resource requirements; use cluster operations for Ray node setup.
- Use `route_prefix` at `serve.run` or application YAML level for user-facing HTTP routes.
- Use `user_config` plus `reconfigure(self, config)` for live parameter changes that should not restart replicas.
- Use `serve status`, `serve config`, and logs to diagnose deployment convergence; do not debug solely from client HTTP failures.
