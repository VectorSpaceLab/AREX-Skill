# Experiment Tracking API Reference

This reference covers the SwanLab APIs owned by the `experiment-tracking` sub-skill. It is intentionally limited to base run tracking; route media objects, credentials/hosts, sync/conversion, and framework callbacks to their sibling sub-skills.

## Public entry points

| API | Typical call | Use |
| --- | --- | --- |
| `swanlab.init` | `swanlab.init(mode="disabled", project="demo", config={...})` | Start exactly one active run. Returns a `swanlab.Run`. |
| `swanlab.log` | `swanlab.log({"loss": 0.5}, step=0)` | Proxy to the active run's `log` method. Requires an active run. |
| `swanlab.finish` | `swanlab.finish()` | Finish the active run, flush pending work, and clear the global run. |
| `swanlab.run` | `if swanlab.run is not None: ...` | Dynamic attribute returning the active run or `None`. |
| `swanlab.get_run` | `run = swanlab.get_run()` | Return the active run; raises `RuntimeError` if none exists. |
| `swanlab.has_run` | `if swanlab.has_run(): ...` | Return `True` only while an active, alive run exists. |
| `swanlab.config` | `swanlab.config["lr"] = 1e-3` | Global config proxy; points at run config while a run is active. |
| `swanlab.save` | `swanlab.save("*.pt", base_path="checkpoints", policy="end")` | Proxy to active run file saving. Requires an active run. |
| `swanlab.async_log` | `swanlab.async_log(compute, step=1)` | Run a callable asynchronously and log the returned dictionary. |
| `swanlab.define_scalar` | `swanlab.define_scalar(key="train/loss")` | Exported symbol, but currently raises `NotImplementedError`; guard before using. |

Top-level methods such as `swanlab.log`, `swanlab.finish`, `swanlab.save`, `swanlab.async_log`, and `swanlab.define_scalar` are wrappers around the current `Run` methods. If there is no active run, wrappers that require a run raise a runtime error.

## `swanlab.init`

Current tracked signature:

```python
swanlab.init(
    *,
    reinit=None,
    log_dir=None,
    mode=None,
    workspace=None,
    project=None,
    public=None,
    name=None,
    color=None,
    description=None,
    job_type=None,
    group=None,
    tags=None,
    id=None,
    resume=None,
    parallel=None,
    config=None,
    settings=None,
    callbacks=None,
    **kwargs,
) -> swanlab.Run
```

Important behavior:

- SwanLab permits one active run per process. Calling `init(reinit=False)` while a run is active raises an error. Use `swanlab.finish()` first or call `swanlab.init(reinit=True, ...)` to finish the previous run before creating a new one.
- `mode` accepts `"online"`, `"local"`, `"offline"`, or `"disabled"`.
  - `disabled`: passive mode for smoke tests and CI; it returns a `Run`, permits logging calls, and should not create the logging directory.
  - `local`: creates local run directories and local dashboard artifacts without cloud upload.
  - `offline`: writes local records intended for later sync.
  - `online`: requires a ready credential/client path and may prompt or fail if credentials are absent.
- `project` defaults to the current directory name if omitted.
- `config` may be a dictionary or a JSON/YAML file path. Loaded values are merged into `run.config` after initialization.
- Compatibility kwargs include `experiment_name` -> experiment name, `notes` -> experiment description, and `logdir` -> `log_dir`.
- In non-disabled modes, SwanLab creates a run directory under `log_dir` and writes supporting files. In disabled mode, it computes a run directory value for internal context but does not create it.
- `init` can be used as a context manager: `with swanlab.init(...) as run:` finishes on exit and marks the run crashed/aborted when an exception or `KeyboardInterrupt` escapes the block.

## Run lifecycle helpers

```python
import swanlab

assert swanlab.run is None
run = swanlab.init(mode="disabled", project="lifecycle-demo")
assert swanlab.has_run()
assert swanlab.run is run
assert swanlab.get_run() is run
swanlab.finish()
assert not swanlab.has_run()
assert swanlab.run is None
```

Use `swanlab.has_run()` in library/helper code that may be called before or after a run:

```python
def maybe_log(metrics, step=None):
    if swanlab.has_run():
        swanlab.log(metrics, step=step)
```

Use `swanlab.get_run()` when no active run is a hard error and you want the explicit exception.

## `Run.log` and `swanlab.log`

Tracked method shape:

```python
run.log(data: Mapping[str, object], step: int | None = None) -> None
swanlab.log({"loss": 0.5, "acc": 0.92}, step=3)
```

Metric data rules:

- `data` must be a mapping/dictionary. Non-mapping values are ignored with an error message.
- Nested dictionaries are flattened with `/`, e.g. `{"train": {"loss": 0.5}}` becomes key `train/loss`.
- Metric keys are sanitized/validated: leading/trailing spaces, dots, and slashes are trimmed; excessive length is truncated; empty or invalid keys are dropped.
- `step` must be `None` or a non-negative integer. Invalid steps are ignored.
- When `step=None`, SwanLab auto-increments the user step. If explicit ordering matters, pass `step` yourself.
- Ordinary scalar values should be numeric, boolean, numeric strings, or scalar tensor/array objects with `.item()`. Convert unsupported objects before logging or route media values to `media-and-custom-charts`.

## Config logging

Use `config` at initialization for stable hyperparameters:

```python
run = swanlab.init(
    mode="offline",
    project="training",
    config={"learning_rate": 3e-4, "batch_size": 32},
)
```

Use `run.config` or `swanlab.config` for values discovered after `init`:

```python
run.config["dataset_version"] = "v2"
swanlab.config.update({"seed": 42})
```

In local/offline modes, config updates are persisted to the run's config file. In disabled mode, config remains in memory. After `finish`, the global config proxy returns to the process-global config rather than the finished run config.

## `finish`

Tracked method shape:

```python
run.finish(state="success", error=None, async_log_timeout=None) -> None
swanlab.finish()
```

- `state` accepts `"success"`, `"crashed"`, or `"aborted"`.
- If `state="crashed"` and `error` is omitted, SwanLab records an `"unknown"` reason.
- `finish` waits for pending `async_log` work before final flush. Use `async_log_timeout` if the background work may hang.
- A second finish on the same run logs a warning and returns. After a normal finish, `swanlab.run` becomes `None`.

## `define_scalar`

Tracked method shape:

```python
run.define_scalar(*, key, name=None, color=None, x_axis=None, chart_name=None)
swanlab.define_scalar(key="train/loss")
```

The API is exported in this package version, but the implementation currently raises:

```text
NotImplementedError: run.define_scalar() is not available yet. Support is planned for a future release.
```

Do not build required workflows around `define_scalar` unless your target SwanLab version has implemented it. Prefer ordinary scalar logging now, and wrap optional calls defensively:

```python
try:
    swanlab.define_scalar(key="train/loss", name="Training loss")
except NotImplementedError:
    pass
```

## `save`

Tracked method shape:

```python
run.save(glob_str, base_path=None, policy="live") -> list[str]
swanlab.save("*.pt", base_path="checkpoints", policy="end")
```

Rules and patterns:

- `glob_str` may be a string, bytes, or `Path`.
- `base_path` controls the relative names stored for matched files. Prefer passing it explicitly so results are stable.
- `policy` accepts:
  - `"now"`: handle matched files immediately.
  - `"end"`: defer handling until `finish`.
  - `"live"`: initial handling plus file watching in modes that support it.
- `save` returns a list of matched file paths relative to `base_path`.
- No matches, invalid patterns, unsupported cloud storage URLs, invalid `base_path`, or invalid policy produce warnings/errors and return `[]`.
- Local/offline modes create local file links under the run file area; online behavior requires credentials/network and is outside this sub-skill's credential guidance.

## `async_log`

Tracked method shape:

```python
run.async_log(func, *args, step=None, mode="threading", **kwargs) -> Future
swanlab.async_log(compute_metrics, step=10)
```

Behavior:

- SwanLab calls `func(*args, **kwargs)` in the requested execution mode.
- When the callable completes successfully, its return value is passed to `log` automatically. Return a dictionary suitable for `swanlab.log`.
- `finish()` waits for outstanding async tasks before the final flush.
- Supported modes:
  - `"threading"` (default): useful for I/O-bound or lightweight work; no pickle constraint.
  - `"asyncio"`: schedules a coroutine on the running event loop; raises `RuntimeError` if no loop is running.
  - `"spawn"`: uses a spawned process; callable, arguments, and return value must be pickle-serializable; child code cannot access the parent active run.
  - `"fork"`: declared in the type surface but currently raises `NotImplementedError`.
- Exceptions inside the async task are traced and do not crash `finish`; they also do not log metrics.

## Fork/process boundary

A `Run` records the process where it was created. After a real `fork`, the child does not own the parent's active run:

- `swanlab.has_run()` is false in the child.
- Calling methods on the inherited parent `Run` raises a fork-safety error.
- Initialize a new SwanLab run inside the child process, or use `async_log(mode="spawn")` with pickle-safe return dictionaries for CPU-bound asynchronous logging.
