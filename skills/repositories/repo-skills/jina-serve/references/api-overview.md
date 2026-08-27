# API Overview

## Verified top-level imports

```python
from jina import Executor, Flow, Deployment, Client, requests
from jina import dynamic_batching, monitor
```

These imports represent the main public surfaces covered by this skill. The installed baseline reported:

- `Flow(args=None, **kwargs)`
- `Deployment(args=None, needs=None, include_gateway=True, **kwargs)`
- `Executor.__init__(metas=None, requests=None, runtime_args=None, workspace=None, dynamic_batching=None, **kwargs)`
- `Client(args=None, **kwargs)` returns a protocol-specific client implementation.

## Route ownership

| API or command | Primary owner | Notes |
|---|---|---|
| `jina --help`, `jina -vf`, `jina help`, `jina export`, `jina new` | [cli-and-configuration](../sub-skills/cli-and-configuration/SKILL.md) | Also covers YAML variables, environment variables, and install variants. |
| `Executor`, `@requests`, `@dynamic_batching`, `@monitor`, `Deployment(uses=...)` for one service | [executor-service-patterns](../sub-skills/executor-service-patterns/SKILL.md) | Use for service logic and single-Executor serving. |
| `Flow`, `Flow.add`, `Flow.config_gateway`, `Flow.load_config`, `Flow.to_kubernetes_yaml`, `Flow.to_docker_compose_yaml` | [orchestration-and-deployment](../sub-skills/orchestration-and-deployment/SKILL.md) | Use for topologies, Gateway protocols, exports, readiness, and profiling. |
| `Client`, `Client.post`, async/streaming clients, callbacks, retries, target executors | [client-and-protocols](../sub-skills/client-and-protocols/SKILL.md) | Use for caller-side request semantics and protocol debugging. |
| `jina ping`, monitoring/tracing args, JCloud/Hub operations, Docker/K8s execution | [observability-and-production](../sub-skills/observability-and-production/SKILL.md) | Use for production health, observability, credentials, and service infrastructure. |

## `Client.post` shape

`Client.post` and the debugging `Flow.post`/`Deployment.post` family accept the same main request options:

```python
post(
    on: str,
    inputs=None,
    on_done=None,
    on_error=None,
    on_always=None,
    parameters=None,
    target_executor=None,
    request_size=100,
    continue_on_error=False,
    return_responses=False,
    max_attempts=1,
    initial_backoff=0.5,
    max_backoff=2,
    backoff_multiplier=1.5,
    results_in_order=False,
    stream=True,
    prefetch=None,
    return_type=DocList,
    **kwargs,
)
```

Use `Client` rather than `Flow.post` in production because remote deployments only expose the network service, not the local Python `Flow` object.

## YAML/config loading

`Executor`, `Deployment`, and `Flow` inherit configuration helpers with a load shape similar to:

```python
Flow.load_config(source, substitute=True, context=None, uses_with=None, uses_metas=None, uses_requests=None, py_modules=None, extra_search_paths=None)
```

Use `substitute=True` and explicit `context={...}` when resolving `${{ CONTEXT.* }}` or relative YAML variables. Use `${{ ENV.VAR }}` for environment variables.
