# Runner Selection

Kedro runners execute a `Pipeline` against a catalog. Choose the runner from the pipeline's dependency shape, dataset/thread/process safety, hook requirements, and deployment environment.

## Built-In Runners

| Runner | Constructor | Best fit | Avoid when |
| --- | --- | --- | --- |
| `SequentialRunner` | `SequentialRunner(is_async=False)` | Default, predictable execution, limited branching, scarce RAM/CPU/disk, debugging failures, thread-unsafe datasets. | Independent branches could benefit from concurrency and datasets are safe for it. |
| `ThreadRunner` | `ThreadRunner(max_workers=None, is_async=False)` | Concurrent node execution with shared process state, Spark workflows sharing one `SparkSession`, hooks that must still run, I/O-bound or GIL-releasing workloads. | Node code or dataset objects are not thread-safe; async load/save is required. |
| `ParallelRunner` | `ParallelRunner(max_workers=None, is_async=False)` | CPU-bound or isolated independent branches where nodes, functions, inputs, and datasets are serializable. | Node/dataset hooks are required, Spark datasets are used, node functions are lambdas/closures/nested functions, datasets are single-process-only, or objects cannot be pickled. |

`AbstractRunner` is the base class for runners. Custom runners should subclass it, implement `_get_executor()` and `_run()` consistently with Kedro's runner contract, and should usually live in the user's project package. Use built-in runners unless the task explicitly needs a dry run, external scheduler handoff, or custom execution engine.

## Selection Checklist

1. Start with `SequentialRunner` for correctness, reproducibility, and diagnosis.
2. Use `ThreadRunner` when nodes can run concurrently in one process and datasets/functions are thread-safe.
3. Use `ThreadRunner` for PySpark-style pipelines where concurrent Spark actions should share one `SparkSession`; `SparkDataset` does not work as expected with `ParallelRunner`.
4. Use `ParallelRunner` only after verifying node functions, datasets, and intermediate values are serializable and hooks are not needed inside worker processes.
5. Use `--async` only for `SequentialRunner` or `ParallelRunner` when datasets can safely load/save in threads and nodes have multiple expensive inputs or outputs.
6. Use `--only-missing-outputs` to resume persisted work; do not use runner choice alone as a resume mechanism.

## Async Load and Save

`is_async=True` changes the load/save phase around node execution. It does not make the node function itself asynchronous.

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --async
KEDRO_DISABLE_TELEMETRY=1 kedro run --runner=ParallelRunner --async
```

Programmatic equivalent:

```python
from kedro.runner import SequentialRunner, ParallelRunner

runner = SequentialRunner(is_async=True)
parallel_runner = ParallelRunner(is_async=True)
```

Use async mode only when all datasets participating in the run are thread-safe. `ThreadRunner(is_async=True)` emits a warning and resets async mode to false because thread execution already uses threads and Kedro does not support async load/save for it.

## Worker Counts

`ThreadRunner(max_workers=None)` and `ParallelRunner(max_workers=None)` estimate required workers from the pipeline topology and CPU count. The required count is bounded by independent groups of nodes and dependencies; a linear pipeline cannot use many workers effectively.

```python
from kedro.runner import ThreadRunner, ParallelRunner

thread_runner = ThreadRunner(max_workers=4)
parallel_runner = ParallelRunner(max_workers=4)
```

`max_workers` must be positive. On Windows, the multiprocessing worker count is capped at 61. For memory-heavy node functions or datasets, a smaller worker count is safer than using all CPU cores.

## Multiprocessing Context

`ParallelRunner` reads `KEDRO_MP_CONTEXT` to choose a multiprocessing start method:

```bash
KEDRO_DISABLE_TELEMETRY=1 KEDRO_MP_CONTEXT=spawn kedro run --runner=ParallelRunner
KEDRO_DISABLE_TELEMETRY=1 KEDRO_MP_CONTEXT=forkserver kedro run --runner=ParallelRunner
KEDRO_DISABLE_TELEMETRY=1 KEDRO_MP_CONTEXT=fork kedro run --runner=ParallelRunner
```

Accepted values are `fork`, `forkserver`, and `spawn`. Invalid values are ignored and the system default is used. `spawn` is usually safest for libraries with threads or complex state, but it requires importable, pickleable functions and objects. `fork` can be faster on platforms where it exists but can be unsafe with libraries that manage internal threads or resources.

## Catalog Choice

When using the CLI or `KedroSession.run()`, Kedro selects the catalog class based on the runner:

```bash
kedro run                         # SequentialRunner with DataCatalog
kedro run --runner=ThreadRunner   # ThreadRunner with DataCatalog
kedro run --runner=ParallelRunner # ParallelRunner with SharedMemoryDataCatalog
```

When calling a runner directly, choose the matching catalog yourself:

```python
from kedro.io import DataCatalog, SharedMemoryDataCatalog
from kedro.runner import SequentialRunner, ThreadRunner, ParallelRunner

SequentialRunner().run(pipeline, DataCatalog.from_config(catalog_config))
ThreadRunner().run(pipeline, DataCatalog.from_config(catalog_config))
ParallelRunner().run(pipeline, SharedMemoryDataCatalog.from_config(catalog_config))
```

`ParallelRunner` validates the catalog for multiprocessing. Dataset classes marked single-process-only, unserializable datasets, or memory dataset contents that cannot be serialized cause failures before or during execution.

## Hooks and Runner Behavior

Project-level pipeline hooks still wrap the overall run through `KedroSession.run()`: `before_pipeline_run`, `after_pipeline_run`, and `on_pipeline_error` are called around the runner execution path.

Node and dataset hooks are runner-sensitive:

- `SequentialRunner` executes node and dataset hooks in the main process.
- `ThreadRunner` executes node and dataset hooks while using threads for runnable node groups.
- `ParallelRunner` does not execute node and dataset hooks in worker processes. Use `SequentialRunner` or `ThreadRunner` when a project relies on those hooks for validation, logging, credentials, dataset mutation, or side effects.

Route hook implementation details to `../hooks-and-extensions/SKILL.md`.

## Programmatic Output Contract

`runner.run(pipeline, catalog)` and `KedroSession.run(...)` return a dictionary keyed by pipeline output dataset names. Values are dataset objects, not raw data.

```python
output_datasets = runner.run(pipeline=pipeline, catalog=catalog)
for name, dataset in output_datasets.items():
    value = dataset.load()
```

Do not assume a node's Python return value is directly returned by the runner. If a node output is saved to a versioned or persistent dataset, load it through the catalog using the desired version rules.

## Runner Choice Examples

### Thread-Unsafe Datasets

Use `SequentialRunner` first when datasets mutate shared in-memory state, use non-thread-safe clients, or cannot tolerate concurrent loads/saves. Add `--async` only after proving dataset thread safety.

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --runner=SequentialRunner
```

### Hooks Required Per Node

Use `SequentialRunner` or `ThreadRunner`. Avoid `ParallelRunner` when node/dataset hooks validate inputs, record metrics, inject credentials, or mutate datasets.

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --runner=ThreadRunner
```

### Spark Workflows

Use `ThreadRunner` to allow multiple nodes to submit Spark actions through the shared Spark session. Avoid `ParallelRunner` with Spark datasets.

```bash
KEDRO_DISABLE_TELEMETRY=1 kedro run --runner=ThreadRunner
```

### CPU-Bound Pure Python Branches

Use `ParallelRunner` only when each node function is importable and serializable, datasets are process-safe, and no worker-level hooks are required.

```bash
KEDRO_DISABLE_TELEMETRY=1 KEDRO_MP_CONTEXT=spawn kedro run --runner=ParallelRunner
```

### Debugging Unknown Failures

Switch to `SequentialRunner`, narrow the slice with `--nodes` or `--from-nodes`, and rerun with telemetry opt-out. After correctness is restored, move back to `ThreadRunner` or `ParallelRunner` if needed.
