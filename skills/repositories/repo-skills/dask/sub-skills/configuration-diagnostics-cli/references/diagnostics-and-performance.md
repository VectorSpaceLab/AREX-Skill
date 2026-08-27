# Local Diagnostics And Performance

Dask's local diagnostics are callback-based tools for the local/threaded/process schedulers. They are useful for progress display, task-level profiling, resource sampling, cache behavior, and custom instrumentation without requiring `distributed`.

## Diagnostic Tools

| Tool | Import | Captures | Typical use |
| --- | --- | --- | --- |
| `ProgressBar` | `from dask.diagnostics import ProgressBar` | Percent complete and elapsed time | Show progress for local `.compute()` calls |
| `Profiler` | `from dask.diagnostics import Profiler` | Task key, task object, start/end times, worker id | Identify slow tasks in a local graph |
| `ResourceProfiler` | `from dask.diagnostics import ResourceProfiler` | Memory and CPU samples | Track process resource use during computation |
| `CacheProfiler` | `from dask.diagnostics import CacheProfiler` | Scheduler cache entry/exit and metric | Understand local scheduler cache lifetime |
| `Callback` | `from dask.callbacks import Callback` | Scheduler lifecycle hooks | Build custom diagnostics |
| `Cache` | `from dask.cache import Cache` | Opportunistic task cache via `cachey` | Reuse intermediate results across computations |

## Progress Bar

```python
from dask.diagnostics import ProgressBar

with ProgressBar(minimum=1.0, width=40):
    result = collection.compute(scheduler="threads")
```

- `minimum` suppresses output for very short computations.
- `width` controls the text bar width.
- `dt` controls update frequency.
- `out` can redirect output to `sys.stderr`, a file-like object, or another stream.
- A `ProgressBar` can be registered globally with `.register()` and removed with `.unregister()`; prefer a context manager for examples and tests.

## Profilers

```python
from dask.diagnostics import CacheProfiler, Profiler, ResourceProfiler

with Profiler() as prof, ResourceProfiler(dt=0.25) as rprof, CacheProfiler() as cprof:
    result = collection.compute(scheduler="threads")

print(prof.results)
print(rprof.results)
print(cprof.results)
```

- `Profiler.results` contains task-level `TaskData` records.
- `ResourceProfiler.results` contains `ResourceData` records and requires `psutil` at runtime.
- `CacheProfiler.results` contains `CacheData` records; use `metric=` and `metric_name=` to track sizes or custom metrics.
- `.visualize()` methods create Bokeh-based plots and require diagnostics visualization dependencies such as `bokeh` and `jinja2`.
- Registered global profilers retain results across computations; call `.clear()` and `.unregister()` when done.

## Custom Callback Hooks

`Callback` supports scheduler hook methods or keyword callbacks:

| Hook | When it runs |
| --- | --- |
| `start(dsk)` / `_start` | Scheduler starts a graph |
| `start_state(dsk, state)` / `_start_state` | Initial scheduler state is ready |
| `pretask(key, dsk, state)` / `_pretask` | Before each task executes |
| `posttask(key, result, dsk, state, id)` / `_posttask` | After each task succeeds |
| `finish(dsk, state, errored)` / `_finish` | Scheduler finishes or errors |

Prefer context managers for scoped instrumentation:

```python
from dask.callbacks import Callback

seen = []

def record_key(key, dsk, state):
    seen.append(key)

with Callback(pretask=record_key):
    result = collection.compute(scheduler="sync")
```

## Opportunistic Cache

```python
from dask.cache import Cache

cache = Cache(1e9)  # bytes-like cache size passed to cachey
cache.register()
try:
    first = collection.compute()
    second = collection.compute()
finally:
    cache.unregister()
```

`Cache` requires the optional `cachey` package. If `cachey` is not importable, constructing `Cache` raises an import-related error explaining that cachey is required.

## Local vs Distributed Diagnostics

Use these tools for local scheduler execution and quick profiling in a single Python process. For cluster dashboards, worker/scheduler metrics, task stream plots, adaptive scaling, and distributed diagnostics, use the `distributed` package documentation and APIs. If `distributed` is not installed, core Dask still supports synchronous, threaded, and multiprocessing schedulers plus the local diagnostics in this reference.

## Safe Local Profiling Workflow

1. Build the Dask collection lazily without calling `.compute()` during graph construction.
2. Choose an explicit local scheduler if reproducibility matters: `scheduler="sync"`, `scheduler="threads"`, or `scheduler="processes"`.
3. Wrap only the final materialization in diagnostic context managers.
4. Inspect `results` lists programmatically before using `.visualize()`.
5. Add optional visualization only after confirming `bokeh` and `jinja2` are installed.
