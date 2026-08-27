# Ray Core API Reference

This reference distills verified Ray Core Python APIs from the public package surface and Ray Core source/docs. It focuses on Python APIs for tasks, actors, object refs, resource options, runtime environments, and local runtime lifecycle.

## Installation and Imports

- Use Python `>=3.10` for current Ray source compatibility.
- Start narrow: `pip install "ray[default]"` for common local Core workflows and CLI/state tooling. Add workflow-specific extras only when needed, such as `ray[data]`, `ray[train]`, `ray[tune]`, `ray[serve]`, or `ray[rllib]`.
- Avoid defaulting to `ray[all]`; it pulls many optional backends that are unnecessary for most Core workloads.

## Runtime Lifecycle

### `ray.init`

Verified signature shape:

```python
ray.init(
    address=None,
    *,
    num_cpus=None,
    num_gpus=None,
    resources=None,
    labels=None,
    object_store_memory=None,
    local_mode=False,
    ignore_reinit_error=False,
    include_dashboard=None,
    dashboard_host="127.0.0.1",
    dashboard_port=None,
    job_config=None,
    configure_logging=True,
    logging_level="info",
    logging_format=None,
    logging_config=None,
    log_to_driver=None,
    namespace=None,
    runtime_env=None,
    enable_resource_isolation=False,
    cgroup_path=None,
    system_reserved_cpu=None,
    system_reserved_memory=None,
    proxy_server_url=None,
    **kwargs,
)
```

Use it to connect the driver to a Ray runtime. With no `address`, Ray checks the environment/current local runtime and otherwise starts a local instance. Use `address="auto"` when the code must attach to an existing cluster and fail if none is found. Use `address="local"` to force a new local runtime. A `ray://...` address requires Ray Client support and connects to a remote cluster endpoint.

Common options:

| Option | Use |
| --- | --- |
| `num_cpus`, `num_gpus` | Override local resource discovery for testing or controlled local scheduling. |
| `resources` | Add custom scalar resources such as `{"node_kind": 1}` for task/actor scheduling. |
| `labels` | Experimental node labels for scheduling selectors. |
| `object_store_memory` | Set local object-store capacity in bytes. Defaults are derived from available memory and shared-memory limits. |
| `namespace` | Group named actors/jobs under a logical namespace. |
| `runtime_env` | Supply per-job dependencies, environment variables, working directory, or Python modules. |
| `include_dashboard`, `dashboard_host`, `dashboard_port` | Control local dashboard startup and binding. Keep host local unless intentionally exposing it. |
| `log_to_driver`, `configure_logging`, `logging_config` | Control worker log forwarding and logging format. |
| `enable_resource_isolation`, `system_reserved_cpu`, `system_reserved_memory` | Experimental cgroupv2 resource isolation for Ray system processes. |

`local_mode` is no longer the recommended debugging path. Prefer small local runs, logging, timeouts, the distributed debugger, and targeted smoke scripts.

### `ray.shutdown`

Verified signature shape:

```python
ray.shutdown(wait_for_processes=False)
```

Use it to disconnect the driver and clean up local processes that were started by `ray.init`. It is safe to call more than once. After shutdown, remote functions, actor classes, and existing actors are cleared from the driver context; redefine or reload them before reuse.

## Remote Tasks

Use `@ray.remote` on a function to create a remote function. Calling `.remote(...)` schedules a task and returns an `ObjectRef` immediately.

```python
import ray

@ray.remote
def parse_record(record):
    return record.strip().upper()

refs = [parse_record.remote(row) for row in rows]
results = ray.get(refs)
```

`ray.remote` verified signature shape:

```python
ray.remote(*args, **kwargs)
```

It returns either a remote-function wrapper or an actor-class wrapper depending on whether the decorated object is a function or class.

Task options can be supplied in the decorator or at call time with `.options(...)`:

```python
@ray.remote(num_cpus=2, max_retries=2, retry_exceptions=False)
def transform(batch):
    return batch

ref = transform.options(num_cpus=1, resources={"special_io": 0.01}).remote(batch)
```

Common task options:

| Option | Notes |
| --- | --- |
| `num_returns` | Number of returned object refs; defaults to `1`, supports multiple returns and generator-related modes. |
| `num_cpus`, `num_gpus` | Resource reservations for scheduling. Defaults are task-dependent; CPU tasks generally reserve one CPU unless configured otherwise. |
| `resources` | Custom scalar resources required to run the task. |
| `accelerator_type` | Require a specific accelerator type. |
| `memory` | Heap-memory scheduling request in bytes. |
| `max_calls` | Limit how many times a worker executes this task before exiting; useful for native-library leaks or GPU cleanup. |
| `max_retries` | Retry worker-process failures; default is `3`, `0` disables, `-1` retries indefinitely. |
| `retry_exceptions` | Retry application exceptions when enabled, subject to `max_retries`. |
| `runtime_env` | Per-task runtime environment inherited by child tasks/actors. |
| `scheduling_strategy` | Default hybrid scheduling, spread, placement group, or node affinity strategies. |
| `enable_task_events` | Emit task events for dashboard/state tooling. |

## Actors

Use `@ray.remote` on a class for stateful workers. Actor construction returns an actor handle; actor method calls return `ObjectRef` values.

```python
@ray.remote
class Counter:
    def __init__(self):
        self.value = 0

    def add(self, amount):
        self.value += amount
        return self.value

counter = Counter.remote()
refs = [counter.add.remote(1) for _ in range(3)]
print(ray.get(refs))  # [1, 2, 3]
```

Methods called on the same default actor execute serially in submission order and share actor state. Methods on different actors can run in parallel.

Common actor options:

| Option | Notes |
| --- | --- |
| `num_cpus`, `num_gpus`, `resources`, `memory` | Reserve resources for the actor lifetime. |
| `object_store_memory` | Object-store memory request for actors. |
| `max_restarts` | Restart unexpectedly dead actors; default `0`, `-1` means indefinitely. |
| `max_task_retries` | Retry actor method calls after actor failure. |
| `max_pending_calls` | Limit queued calls per actor handle to prevent unbounded backlogs. |
| `max_concurrency` | Allow concurrent actor method execution; defaults to serial execution for threaded actors. Ordering is not guaranteed when greater than `1`. |
| `name`, `namespace`, `lifetime` | Create retrievable named actors; `lifetime="detached"` decouples actor lifetime from creator fate. |
| `runtime_env` | Actor and child-task runtime environment. |
| `scheduling_strategy` | Placement or node-affinity scheduling. |

Use `ray.method(num_returns=...)` on actor methods that return multiple object refs.

## Object APIs

### `ray.put`

Use `ray.put(value)` to put a Python object into Ray's distributed object store and get an `ObjectRef`. Remote objects are immutable and tracked by distributed reference counting.

```python
large_lookup_ref = ray.put(large_lookup_table)
```

Use `ray.put` for large immutable values reused by many tasks or actors. Avoid returning `ray.put(...)` from inside a task; return the value directly so Ray owns lineage and memory more predictably.

### `ray.get`

Verified signature shape:

```python
ray.get(object_refs, *, timeout=None)
```

It accepts one `ObjectRef` or a sequence of refs. It blocks until values are available or raises a timeout error when `timeout` is set.

```python
value = ray.get(one_ref)
values = ray.get(list_of_refs)
```

Use `ray.get` at synchronization boundaries, not immediately after every task submission. For many or memory-heavy refs, process in batches with `ray.wait`.

### `ray.wait`

Verified signature shape:

```python
ready, unready = ray.wait(ray_waitables, *, num_returns=1, timeout=None, fetch_local=True)
```

`ray.wait` returns two lists: ready refs and not-yet-ready refs. Use it to poll partial results, bound memory, implement backpressure, and consume outputs in completion order.

```python
pending = [work.remote(item) for item in items]
while pending:
    ready, pending = ray.wait(pending, num_returns=1)
    result = ray.get(ready[0])
    handle(result)
```

## Object Reference Passing Semantics

- Top-level `ObjectRef` arguments are dereferenced before task or actor method execution. The remote function receives the concrete value.
- Nested refs inside containers are not automatically dereferenced. The remote function receives a container holding refs and must call `ray.get` if it needs the values.
- Closure-captured refs pin the referenced object for the lifetime of the remote function/actor definition in the job. Prefer explicit arguments for objects that should be released.
- Nested objects that contain refs keep inner objects alive until outer refs and contained refs are no longer referenced.

## Runtime Environment Basics

Use `runtime_env` to make dependencies and environment variables available to workers:

```python
ray.init(runtime_env={"env_vars": {"MODE": "dev"}})

@ray.remote(runtime_env={"pip": ["requests==2.32.0"]})
def fetch(url):
    import requests
    return requests.get(url, timeout=5).status_code
```

Practical rules:

- Prefer a job-level `runtime_env` in `ray.init` for common dependencies and env vars.
- Use per-task or per-actor `runtime_env` only when a subset of work needs different dependencies.
- Keep working directories small and explicit. Exclude large data, virtual environments, model weights, generated outputs, and caches.
- Runtime env setup happens before workers execute; startup latency can dominate tiny tasks.
- Do not rely on the driver process's local imports unless the code is packaged, installed, or included in `runtime_env`.
