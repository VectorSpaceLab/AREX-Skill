# Ray Core Troubleshooting

Use this guide for Python Ray Core failures and performance pathologies in tasks, actors, object refs, local runtime startup, and resource scheduling.

## Symptom Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Work runs sequentially despite `@ray.remote` | `ray.get` is called immediately inside the submission loop | Submit refs first; call `ray.get(refs)` after submission or poll with `ray.wait`. |
| Driver hangs on `ray.get` | Task is slow, stuck, unscheduled, failed with hidden logs, or waiting on nested refs | Add `timeout`, inspect the failing ref, reduce resources, check worker logs, and replace nested `ray.get` with top-level dependencies. |
| Object-store OOM or heap OOM at the driver | Fetching too many large objects at once or retaining refs/values | Use `ray.wait` batches, write/process outputs incrementally, and delete consumed refs and values. |
| Objects never evict | Refs are pinned in driver lists, actor fields, nested objects, closures, or global variables | Track ref ownership; avoid closure-capturing large refs; delete or overwrite long-lived references. |
| Task never schedules | Requested resources exceed cluster availability or custom resource names do not exist | Compare task/actor resource options with `ray.available_resources()` and lower or correct reservations. |
| Actor calls pile up | Single actor is serial by default or handle has unbounded pending calls | Add more actor replicas, use `max_pending_calls`, or use `max_concurrency` only when state is safe. |
| Serialization error | Function, class, argument, closure, or return value is not cloudpickle-serializable | Move definitions to module scope, remove open handles/locks/sockets from arguments, and pass simple data or actor handles. |
| Worker exits or task is retried repeatedly | Native library crash, process OOM, incompatible dependency, or non-idempotent exception retry | Inspect exception from `ray.get`, reduce memory, set `max_calls`, pin dependencies via `runtime_env`, and disable unsafe retries. |
| Local tests contaminate each other | `ray.shutdown()` missing or remote definitions reused after shutdown | Use `try/finally: ray.shutdown()` and redefine remote functions/classes after shutdown. |
| Worker cannot import local module | Code is only present on the driver and not packaged for workers | Install the package or provide a minimal `runtime_env` with a small working directory/modules. |

## Blocking `ray.get`

Bad pattern:

```python
results = []
for item in items:
    results.append(ray.get(process.remote(item)))
```

This serializes the workflow because each task must finish before the next task is submitted.

Fix:

```python
refs = [process.remote(item) for item in items]
results = ray.get(refs)
```

For uneven or large results:

```python
pending = [process.remote(item) for item in items]
while pending:
    ready, pending = ray.wait(pending, num_returns=4, timeout=10)
    if not ready:
        raise TimeoutError("No Ray task finished within 10 seconds")
    consume(ray.get(ready))
```

Triage steps:

1. Add `timeout` to `ray.get` or `ray.wait` so the driver can report a useful error.
2. Check whether the task requested impossible resources.
3. Check whether the task is blocked on another `ray.get` inside a worker.
4. Reduce input size to a single task and verify serialization/imports.
5. If the task has side effects, make retries idempotent before increasing retry counts.

## Nested `ray.get` and ObjectRef Arguments

Problem pattern:

```python
@ray.remote
bad_consumer(refs):
    value = ray.get(refs[0])
    return use(value)

bad_consumer.remote([producer.remote()])
```

Because the ref is nested in a list, Ray passes the `ObjectRef` itself. The task then blocks a worker process while it calls `ray.get`.

Better:

```python
@ray.remote
def consumer(value):
    return use(value)

consumer.remote(producer.remote())
```

A top-level `ObjectRef` argument creates a dependency edge. Ray waits for the producer result before running the consumer and passes the concrete value.

Nested refs are valid when the callee intentionally forwards refs or chooses a fetch order, but they should be a deliberate design choice.

## Object Store Memory Pressure

Common causes:

- `ray.get` materializes too many large results at once in the driver.
- A list of `ObjectRef` values is retained after outputs are consumed.
- Large refs are captured in remote function/class closures.
- Actors store many refs or large values in fields without eviction logic.
- Nested objects hold refs and keep inner objects alive.

Mitigations:

```python
pending = submit_initial_work()
while pending:
    ready, pending = ray.wait(pending, num_returns=8)
    outputs = ray.get(ready)
    write_and_forget(outputs)
    del outputs, ready
```

Additional fixes:

- Batch tiny outputs into fewer medium-sized objects.
- Stream or write large results to durable storage instead of returning all data to the driver.
- Prefer explicit argument passing over closure capture for large refs.
- Delete actor-held refs after use or rotate actors when third-party libraries leak memory.
- Increase `object_store_memory` only after reducing avoidable pinning/fetching.

## Closure-Captured ObjectRefs

Problem:

```python
large_ref = ray.put(load_large_table())

@ray.remote
def lookup(key):
    table = ray.get(large_ref)  # large_ref stays pinned for the job lifetime.
    return table[key]
```

Fix:

```python
@ray.remote
def lookup(key, table):
    return table[key]

large_ref = ray.put(load_large_table())
refs = [lookup.remote(key, large_ref) for key in keys]
```

When done, delete `large_ref` and any containers holding it.

## Serialization Failures

Ray serializes remote functions/classes, arguments, closures, and return values. Failures often involve local definitions, locks, file handles, sockets, clients, generators, or native objects.

Fix checklist:

- Define remote functions/classes at module scope.
- Avoid capturing `self` from a large driver object; pass only needed fields.
- Initialize non-serializable clients inside an actor `__init__` instead of passing them as arguments.
- Return plain Python data, NumPy arrays, pandas objects, or explicit file/URI metadata rather than open handles.
- Test `ray.put(suspect_value)` to isolate argument serialization issues.

## Resource Deadlocks and Unschedulable Work

Symptoms:

- Pending tasks never run.
- Actor creation hangs.
- Parent tasks wait on child tasks while all resources are occupied.

Checks:

```python
print(ray.cluster_resources())
print(ray.available_resources())
```

Fixes:

- Lower `num_cpus`, `num_gpus`, `memory`, or custom resource requests.
- Ensure custom resource names in task options match resources advertised at startup.
- Move orchestration that waits on children back to the driver.
- For nested task trees, reserve fewer resources in parent tasks or use actors/queues to bound concurrency.
- Avoid creating actors that each reserve all CPUs unless only one actor should run.

## Actor Failures and Concurrency Bugs

Default actors execute one method at a time, preserving state consistency. Increasing concurrency can introduce races and out-of-order execution.

Use these patterns:

- Scale by creating more actors before increasing `max_concurrency`.
- Use `max_concurrency` only for stateless, thread-safe, or async-safe methods.
- Use `max_pending_calls` when producers can flood actor handles.
- Use `max_restarts` for reconstructible actors and make `__init__` deterministic.
- Store checkpoints or durable state outside the actor if state must survive restarts.

## Worker or System Exit

When `ray.get(ref)` raises a worker/system exception:

1. Read the exception type and message from the `ray.get` call.
2. Check whether the task exceeded memory or crashed native code.
3. If a GPU/native framework leaks state, use `max_calls=1` or a low `max_calls` value.
4. If a runtime dependency differs across workers, pin it in `runtime_env` or the environment used to start the cluster.
5. If application exceptions should not retry, keep `retry_exceptions=False` and fix the underlying error.
6. If the operation is idempotent and transient, set bounded `max_retries` and optionally `retry_exceptions=True`.

## Runtime Environment Failures

Common signals:

- Worker import succeeds on the driver but fails remotely.
- Runtime env setup is slow for every task.
- A package version differs between driver and workers.

Fixes:

- Put common dependencies in job-level `ray.init(runtime_env=...)` rather than per-task overrides.
- Keep uploaded working directories small; exclude data, virtual environments, caches, and generated files.
- Install reusable project code as a package when possible.
- Avoid changing `runtime_env` per call unless isolation is worth the setup cost.
- Keep secrets out of `runtime_env` definitions committed to code.

## Cleanup Between Runs

Use a cleanup guard in scripts and tests:

```python
import ray

try:
    ray.init(include_dashboard=False)
    # Ray work here.
finally:
    ray.shutdown()
```

If reusing a Python process after `ray.shutdown`, redefine remote functions/classes or reload the module that defines them. Existing actor handles and refs from the previous runtime are no longer valid.
