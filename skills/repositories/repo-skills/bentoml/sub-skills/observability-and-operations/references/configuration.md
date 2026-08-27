# Operational Configuration, Scaling, and Testing

## Runtime Configuration Model

Modern BentoML services configure runtime behavior directly on `@bentoml.service(...)`. Specify only the fields that need customization; BentoML fills unspecified values from defaults.

Common operational fields:

```python
import bentoml

@bentoml.service(
    resources={"cpu": "2", "memory": "4Gi", "gpu": 1, "gpu_type": "nvidia-l4"},
    workers=2,
    traffic={
        "timeout": 120,
        "max_concurrency": 50,
        "concurrency": 32,
        "external_queue": True,
    },
    runner_probe={"enabled": True, "timeout": 1, "period": 10},
    metrics={"enabled": True, "namespace": "bentoml_service"},
    logging={"access": {"enabled": True}},
)
class MyService:
    ...
```

Key separation:

- Local/runtime controls: `workers`, `traffic.timeout`, `traffic.max_concurrency`, health endpoints, logging, metrics, monitoring, tracing, and code-level GPU selection.
- BentoCloud controls: `resources`, `resources.gpu_type`, `traffic.concurrency`, `traffic.external_queue`, deployment scaling min/max, scaling policy windows, and gateways.
- Packaging controls such as `image`, Python packages, CUDA library selection, and build/container settings belong to packaging guidance, but operational plans should call out when missing packages make telemetry or GPU runtime impossible.

## Resource Settings

`resources` can include:

- `cpu`: string/int/float such as `"500m"`, `"1"`, or `2`.
- `memory`: string/int/float such as `"4Gi"`.
- `gpu`: positive number of GPUs.
- `gpu_type`: BentoCloud GPU SKU such as `nvidia-l4` or `nvidia-tesla-a100`.
- `tpu_type`: TPU type when applicable.

Important caveat: the documented `resources` field is primarily a BentoCloud resource allocation signal. Local GPU use still depends on the machine/container runtime, framework installation, CUDA visibility, and code that moves models/tensors to the selected device.

## Workers and Concurrency

`workers` controls process-level parallelism inside a service instance. It defaults to `1` and may be an integer or `"cpu_count"`.

Use workers when:

- CPU-bound Python code needs multiple processes to bypass GIL limits.
- Each worker can afford its own model copy in memory.
- A multi-GPU host should map one worker to one GPU.

GPU worker pattern:

```python
@bentoml.service(resources={"gpu": 2}, workers=2)
class MyService:
    def __init__(self):
        import torch
        device = torch.device(f"cuda:{bentoml.server_context.worker_index - 1}")
        self.model = load_model().to(device)
```

Operational caution: BentoML `server_context.worker_index` is 1-indexed in the documented worker/GPU pattern, while CUDA device IDs are 0-indexed.

`traffic` controls request handling:

- `timeout`: response timeout in seconds; default is 60 seconds.
- `max_concurrency`: hard local limit for simultaneous requests per service instance.
- `concurrency`: BentoCloud ideal concurrent requests per service; drives autoscaling.
- `external_queue`: BentoCloud request queue for excess traffic; requires `concurrency`.

Choose values by stress testing rather than guessing. For adaptive/continuous batching, align BentoCloud `traffic.concurrency` with effective batch size or capacity. For one-request-at-a-time services, set concurrency to `1`.

## GPU Operations

For GPU services, plan three layers separately:

1. Runtime image/package layer: framework packages such as `torch` or `tensorflow[and-cuda]`, optional CUDA libraries, and compatible base image.
2. Scheduling layer: `resources={"gpu": N, "gpu_type": "..."}` for BentoCloud, or container runtime GPU flags locally.
3. Application layer: model/tensor placement with `cuda`, `cuda:0`, `cuda:1`, or framework-specific distributed APIs.

Local/container checks:

- Run `nvidia-smi` on the host/container when available to confirm driver and device visibility.
- For Docker GPU containers, the runtime must expose GPUs, for example with `--gpus all`; BentoML service config alone cannot expose host devices.
- Use `CUDA_VISIBLE_DEVICES` to restrict visible devices before starting the service when testing device placement.
- If a service has multiple workers and one GPU, confirm memory can hold multiple model copies or reduce worker count.

## Health Probes and Runner Probes

BentoML exposes `/livez`, `/readyz`, and `/healthz` by default. `runner_probe` controls health check behavior on BentoCloud for these probes:

```python
@bentoml.service(runner_probe={"enabled": True, "timeout": 1, "period": 10})
class MyService:
    ...
```

Use health probes to distinguish:

- process/server not started: health endpoints fail or connection refused;
- service loading not ready: readiness fails;
- telemetry only missing: health endpoints pass while `/metrics` or collector output is wrong;
- upstream gateway/routing issue: direct deployment health passes while gateway endpoint fails.

## BentoCloud Autoscaling

BentoCloud autoscaling reacts to incoming traffic and concurrency within deployment min/max replicas.

Required planning inputs:

- Service `traffic.concurrency`: ideal simultaneous requests per replica.
- Deployment scaling min/max: boundaries for replica count.
- Scale-to-zero: set minimum replicas to `0` in deployment configuration.
- External queue: enable only when queueing excess requests is acceptable; it adds latency.
- Policy windows: use scale-up/down stabilization windows from 0 to 3600 seconds to dampen flapping.

Policy config shape:

```yaml
services:
  MyService:
    scaling:
      min_replicas: 1
      max_replicas: 4
      policy:
        scale_up_stabilization_window: 180
        scale_down_stabilization_window: 600
```

Operational rules:

- If `traffic.concurrency` is unset, BentoCloud may autoscale based mainly on CPU utilization, which can be poor for GPU/LLM services.
- If `external_queue` is enabled, set `traffic.concurrency`; otherwise excess-request behavior is undefined or invalid for the intended design.
- With scale-to-zero, the request may sit in the external queue while the service scales up; use `/readyz` to manually trigger scale-up if needed.
- Keep local `max_concurrency` and BentoCloud `concurrency` conceptually separate: one is a runtime guard, the other is an autoscaling target.

## Gateways

BentoCloud Gateways expose one stable endpoint across multiple upstream Deployments, often spanning clouds, regions, or GPU providers. They route by protocol, model/request parameters, and configured load balancing strategy.

Gateway planning fields:

- Name and domain for the endpoint.
- Protocol, such as OpenAI Chat Completions when routing by `model` field.
- Load balancing strategy: overflow routing or capacity-based round robin.
- Upstream deployments, regions, and capacity assumptions.
- Failover and overflow behavior when baseline committed capacity is exhausted.

Operational guardrails:

- Gateways are external BentoCloud resources and require cloud credentials and account configuration; local scripts in this skill do not create or modify them.
- Debug upstream deployment health and direct endpoint behavior before changing gateway routing.
- When only gateway traffic fails, compare protocol compatibility, model names/request parameters, and upstream deployment readiness.

## Operational Testing

Use the lightest test that exercises the relevant layer:

- Unit test: instantiate the service and mock large models or external dependencies.
- ASGI/HTTP behavior test: use `Service.to_asgi()` with Starlette `TestClient` for route/status behavior.
- Local integration test: start `bentoml serve` on an unused port and call it with `bentoml.SyncHTTPClient`.
- Health/metrics smoke: call `/livez`, `/readyz`, `/healthz`, and `/metrics` after generating traffic.
- BentoCloud E2E: create a temporary deployment, wait for readiness, call it, then terminate/delete it. This requires credentials and may incur cost.

Safe operational assertions:

- Health endpoints return HTTP 200.
- `/metrics` contains `bentoml_service_request_total` after at least one request.
- Custom metric families appear after the code path observes or increments them.
- Access logs skip health/metrics paths when `skip_paths` includes them.
- Tracing collector receives spans only when exporter dependencies, `sample_rate`, endpoint, and environment variables are correct.
