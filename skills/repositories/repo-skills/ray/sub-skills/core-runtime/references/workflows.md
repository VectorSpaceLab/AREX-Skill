# Ray Core Workflows

Use these recipes to convert local Python work into Ray Core tasks, actors, and object pipelines without depending on external examples.

## Start a Safe Local Session

```python
import ray

if not ray.is_initialized():
    ray.init(num_cpus=4, include_dashboard=False)

try:
    # Submit tasks and actors here.
    ...
finally:
    ray.shutdown()
```

Guidelines:

- Use `ray.init()` once per driver process. If tests call it repeatedly, pair each test with `ray.shutdown()`.
- Pass `num_cpus` in local tests to make scheduling predictable.
- Disable the dashboard for short local smokes unless dashboard behavior is the target.
- Avoid `local_mode`; it is not the modern Core debugging path.

## Convert a Pure Function to Tasks

Start with a pure-ish function whose inputs and outputs are serializable.

```python
@ray.remote(num_cpus=1)
def score(record, model_config):
    return run_score(record, model_config)

refs = [score.remote(record, config) for record in records]
results = ray.get(refs)
```

Checklist:

- Keep each task large enough to amortize scheduling overhead. If a call takes only microseconds or a few milliseconds, batch inputs.
- Submit work first, then synchronize. Do not call `ray.get(score.remote(x))` inside the submission loop.
- Return plain serializable values, arrays, or small metadata. Store large shared read-only inputs with `ray.put` and pass refs directly.
- Use `max_retries` for worker crashes and `retry_exceptions=True` only when retrying application exceptions is safe and idempotent.

## Process Results with `ray.wait`

Use completion-order polling when results are uneven or memory-heavy.

```python
pending = [score.remote(record, config) for record in records]
completed = []

while pending:
    ready, pending = ray.wait(pending, num_returns=min(8, len(pending)))
    batch = ray.get(ready)
    completed.extend(batch)
    del batch, ready
```

Why this helps:

- Avoids waiting for slow tasks before consuming fast results.
- Prevents `ray.get(all_refs)` from materializing too many large objects in the driver heap at once.
- Lets the driver apply backpressure by submitting more work only after processing ready results.

Bound pending work for streaming inputs:

```python
max_pending = 64
pending = []

for item in source:
    pending.append(score.remote(item, config))
    if len(pending) >= max_pending:
        ready, pending = ray.wait(pending, num_returns=16)
        consume(ray.get(ready))

while pending:
    ready, pending = ray.wait(pending, num_returns=min(16, len(pending)))
    consume(ray.get(ready))
```

## Convert Stateful Code to Actors

Use actors for mutable state, expensive setup, connection pools, or objects that should stay on one worker.

```python
@ray.remote(num_cpus=1, max_restarts=1, max_task_retries=1)
class ModelWorker:
    def __init__(self, weights_ref):
        self.weights = ray.get(weights_ref)
        self.count = 0

    def predict(self, batch):
        self.count += len(batch)
        return infer(self.weights, batch)

    def stats(self):
        return {"processed": self.count}

weights_ref = ray.put(load_weights())
workers = [ModelWorker.remote(weights_ref) for _ in range(4)]
refs = [workers[i % len(workers)].predict.remote(batch) for i, batch in enumerate(batches)]
results = ray.get(refs)
```

Actor design rules:

- Default actor methods on the same actor are serial. Create multiple actor instances for parallelism.
- Use `max_concurrency` or async actors only after checking state safety and ordering requirements.
- Use `max_pending_calls` to prevent a single handle from queuing unbounded work.
- Use named actors only when another process must retrieve them. Pair names with `namespace` deliberately.
- Use detached actors only for long-lived services; otherwise let actors fate-share with their creator.

## Resource Scheduling Recipes

### CPUs and GPUs

```python
@ray.remote(num_cpus=2)
def cpu_heavy(batch):
    return transform(batch)

@ray.remote(num_gpus=0.5, max_calls=1)
def gpu_infer(batch):
    return infer_on_gpu(batch)
```

- Resource values are scheduling reservations, not hard OS limits for ordinary Python code.
- Fractional GPU reservations can colocate work but require the code to avoid overusing GPU memory.
- GPU tasks often use `max_calls=1` to release framework state after each worker exits.

### Custom Resources

Start Ray with a custom resource and require it on selected work:

```python
ray.init(resources={"special_io": 2})

@ray.remote(resources={"special_io": 1})
def read_from_limited_device(path):
    return read(path)
```

Use custom resources for logical constraints such as limited licenses, special hardware, or throttled external systems. Keep quantities simple and documented.

### Avoid Resource Deadlocks

Deadlock-prone pattern:

```python
@ray.remote(num_cpus=1)
def parent(x):
    child_ref = child.remote(x)
    return ray.get(child_ref)  # Parent holds worker memory while waiting.
```

Better: express dependencies through top-level refs or split orchestration to the driver.

```python
child_refs = [child.remote(x) for x in xs]
parent_refs = [parent.remote(child_ref) for child_ref in child_refs]  # top-level ref dependency
```

## Object Store Usage

### Share Large Read-Only Inputs

```python
lookup_ref = ray.put(load_lookup_table())
refs = [score.remote(record, lookup_ref) for record in records]
```

Pass `lookup_ref` as a top-level argument so Ray fetches the value before task execution. Do not capture it in the remote function closure unless the object should remain pinned until the job ends.

### Keep Refs Short-Lived

```python
ready, pending = ray.wait(pending, num_returns=8)
outputs = ray.get(ready)
write_outputs(outputs)
del outputs, ready
```

Refs held in driver lists, actor fields, nested objects, closures, or pending queues keep objects alive. Delete refs and consumed values when memory pressure matters.

### Choose Top-Level vs Nested Refs

```python
@ray.remote
def needs_value(value):
    return use(value)

@ray.remote
def forwards_ref(refs):
    # refs[0] is still an ObjectRef because it was nested in a list.
    return downstream.remote(refs[0])

value_ref = ray.put(data)
needs_value.remote(value_ref)       # task receives data
forwards_ref.remote([value_ref])    # task receives [ObjectRef]
```

Use top-level refs when the callee needs the value. Use nested refs only when intentionally forwarding refs or choosing when to fetch inside the callee.

## Runtime Environment Recipes

### Job-Level Environment

```python
ray.init(runtime_env={
    "env_vars": {"APP_MODE": "batch"},
    "pip": ["pydantic==2.11.0"],
})
```

Use this when all tasks/actors need the same dependencies.

### Per-Task or Per-Actor Environment

```python
@ray.remote(runtime_env={"env_vars": {"MODEL_VARIANT": "small"}})
def run_variant(record):
    return record
```

Use this only for specialized work. Per-call environment changes add setup overhead and can create confusing dependency differences between workers.

### Working Directory Cautions

- Package reusable code as an installable module when possible.
- Keep `working_dir` small; avoid uploading datasets, checkpoints, virtual environments, `.git`, caches, and generated outputs.
- Use excludes when packaging a directory.
- If workers fail to import local modules, treat that as a packaging/runtime-env issue, not a Ray scheduler issue.

## Fault Tolerance Basics

Tasks:

```python
@ray.remote(max_retries=3, retry_exceptions=False)
def robust_io(item):
    return call_idempotent_service(item)
```

Actors:

```python
@ray.remote(max_restarts=2, max_task_retries=1)
class Worker:
    def step(self, item):
        return item
```

Rules:

- Task retries handle worker process crashes by default. Application exceptions are retried only when enabled.
- Actor restarts recreate actor state by rerunning `__init__`; persist or reconstruct critical state explicitly.
- Retried side effects can duplicate writes. Add idempotency keys or move writes to a controlled sink.
- Use `ray.get(..., timeout=seconds)` for driver-side bounded waits and surface stalled work cleanly.

## Rewrite Common Anti-Patterns

| Anti-pattern | Rewrite |
| --- | --- |
| `ray.get(task.remote(x))` inside a loop | Submit all refs first, then `ray.get(refs)` or poll with `ray.wait`. |
| `ray.get(all_large_refs)` | Use `ray.wait` and process small batches. |
| Passing `[ref]` then calling `ray.get` inside task | Pass `ref` as a top-level argument if the callee needs the value. |
| Capturing `large_ref` in a remote function closure | Pass `large_ref` explicitly and delete it when no longer needed. |
| Millions of tiny tasks | Batch inputs or move stateful loops into actors. |
| Redefining `@ray.remote` inside a hot loop | Define remote functions/classes once at module scope. |
| Returning `ray.put(result)` from tasks | Return `result` directly. |
| Blocking actor method waiting on same actor | Split methods, use another actor, or orchestrate dependencies in the driver. |

## End-to-End Pattern: Serial Function to Ray Tasks

Original serial shape:

```python
outputs = []
for item in items:
    outputs.append(transform(item, config))
```

Ray Core shape:

```python
config_ref = ray.put(config)
refs = [transform_remote.remote(item, config_ref) for item in items]
outputs = []

while refs:
    ready, refs = ray.wait(refs, num_returns=min(16, len(refs)))
    outputs.extend(ray.get(ready))
```

Remote definition:

```python
@ray.remote(num_cpus=1, max_retries=2)
def transform_remote(item, config):
    return transform(item, config)
```

If `transform` has expensive reusable setup, switch to an actor pool:

```python
actors = [TransformActor.remote(config_ref) for _ in range(4)]
refs = [actors[i % 4].transform.remote(item) for i, item in enumerate(items)]
```
