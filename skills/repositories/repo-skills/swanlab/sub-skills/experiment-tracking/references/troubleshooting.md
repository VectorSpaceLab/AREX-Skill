# Experiment Tracking Troubleshooting

Use this guide for base SwanLab run tracking failures. For credential storage, host selection, sync, media objects, and framework callbacks, route to the matching sibling sub-skill.

## Quick diagnosis table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `RuntimeError: No active Run. Call swanlab.init() first.` | `swanlab.get_run()` was called before `init` or after `finish`. | Start a run, guard with `swanlab.has_run()`, or move code before `finish`. |
| `` `run.log()` requires an active Run, call `swanlab.init()` first. `` | `swanlab.log` proxied to no alive run. | Use `with swanlab.init(...):` or `if swanlab.has_run(): swanlab.log(...)`. |
| `` `swanlab.init` requires an inactive Run `` | A run is already active and `reinit=False`. | Call `swanlab.finish()` first or pass `reinit=True` for sequential runs. |
| `swanlab.run is None` after `finish` | Normal lifecycle behavior. | Reinitialize with `swanlab.init(...)` before logging again. |
| Second `finish()` prints a warning | Finish is intentionally idempotent on a non-alive run. | Remove duplicate finish calls or guard with `swanlab.has_run()`. |
| Disabled smoke creates no files | Expected for `mode="disabled"`. | Use `local` or `offline` when you need local run records. |
| Local/offline init fails with permission error | `log_dir` is unwritable. | Choose a writable `log_dir` or fix directory permissions. |
| Online init fails due API key/no TTY/network | Online mode needs credential/client setup and may need network. | Use `disabled`, `local`, or `offline` for credential-safe work; route credential setup to `settings-and-modes`. |
| `async_log(mode="asyncio")` raises `RuntimeError` | No event loop is running. | Call from inside an event loop, or use `mode="threading"`. |
| `async_log(mode="spawn")` fails to pickle | Callable, args, or return value is not pickle-safe. | Use a top-level function and plain return dict, or use `threading`. |
| `async_log(mode="fork")` raises `NotImplementedError` | Fork mode is reserved in this version. | Use `threading`, `asyncio`, or `spawn`; initialize a new run in child processes. |
| Child process cannot log to parent run | SwanLab detects forked inherited runs. | Initialize SwanLab inside the child or return data to the parent for logging. |
| `define_scalar` raises `NotImplementedError` | API is exported but not implemented in this version. | Treat it as optional and use ordinary scalar logging. |
| `save` returns `[]` | Glob matched no files, invalid path/base path, unsupported URL, or invalid policy. | Check file existence, pass `base_path`, and use `now`, `end`, or `live`. |

## No active run

Most top-level tracking functions are proxies to the current active `Run`. This fails before `init`, after `finish`, or in forked children.

Safe helper:

```python
def log_if_active(metrics, step=None):
    if swanlab.has_run():
        swanlab.log(metrics, step=step)
```

Strict helper:

```python
run = swanlab.get_run()  # raise if no active run
run.log({"metric": 1.0})
```

If the user reports `swanlab.run is None` after a run finished, explain that this is expected: `finish()` clears the global run. Start a new run before more logging.

## Double init or double finish

Double init without `reinit=True`:

```python
swanlab.init(mode="disabled")
swanlab.init(mode="disabled")  # RuntimeError
```

Fix sequential runs:

```python
swanlab.init(mode="disabled")
swanlab.finish()
swanlab.init(mode="disabled")
```

or:

```python
swanlab.init(mode="disabled", reinit=True)
```

Double finish is not fatal. A second call warns that the run has already finished or has not started. Prefer one of these patterns:

```python
with swanlab.init(mode="offline"):
    train()
```

or:

```python
run = swanlab.init(mode="offline")
try:
    train()
finally:
    if swanlab.has_run():
        swanlab.finish()
```

## Mode confusion: disabled, local, offline, online

- `disabled`: returns a valid `Run` and accepts logging calls, but uses null components and does not create log/media files. Best for tests and smoke checks.
- `local`: creates local run files and local visualization artifacts. It does not need cloud upload for base tracking, but it does need a writable `log_dir`.
- `offline`: creates local run records intended for later sync. The sync step is owned by `sync-and-converters`.
- `online`: intended for cloud tracking. It requires credential/client readiness and may fail in non-interactive or no-network environments.

When adapting cloud-oriented examples, choose `mode="disabled"` for pure API smoke tests and `mode="offline"` or `"local"` when the user wants records on disk.

## Unwritable `log_dir`

Local/offline/online modes create directories. If `init` fails with a permission error, do not ignore it; the run did not start cleanly.

Fixes:

```python
run = swanlab.init(mode="offline", log_dir="./runs/swanlab")
```

or choose a known writable temporary/output directory in the user's project. In restricted CI, use `mode="disabled"` if filesystem records are not required.

## API key or network failures

This sub-skill intentionally does not provide credential setup. For base tracking code:

- Use `mode="disabled"`, `"local"`, or `"offline"` when credentials are absent.
- Do not hard-code API keys in examples.
- Do not switch a safe example to `online` unless the user has already handled login/API-key settings.
- Route custom host/API-key/login questions to `settings-and-modes`.

## Invalid metric data

SwanLab accepts mapping-style log data:

```python
swanlab.log({"train/loss": 0.5}, step=0)
```

Common issues:

- Data is not a dict/mapping: convert it to `{"name": value}`.
- `step` is negative or not an integer: use `None` for auto-step or pass a non-negative `int`.
- Key sanitization trims leading/trailing spaces, dots, and slashes. Keys that become empty are dropped.
- Nested dictionaries flatten with `/`; watch for duplicate keys after flattening/sanitization.
- Scalar values should be numeric, boolean, numeric strings, or scalar tensor/array objects. Convert unsupported tensors/arrays with `.item()` or `float(...)`.
- Rich objects belong in `media-and-custom-charts`, not base scalar troubleshooting.

## Config file problems

`init(config=...)` accepts a dictionary or JSON/YAML path. Failures occur when:

- The file does not exist.
- The suffix/content cannot be parsed as JSON or YAML.
- The value is neither a mapping nor a path-like object.

Safe pattern:

```python
config = {"lr": 3e-4, "epochs": 10}
run = swanlab.init(mode="offline", project="demo", config=config)
```

For runtime-discovered values, update config after init:

```python
run.config["dataset_size"] = len(dataset)
```

## `save` troubleshooting

If `run.save(...)` returns an empty list or does nothing visible:

1. Confirm a run is active.
2. Confirm the target files exist before `save` runs.
3. Pass an explicit `base_path` so the glob resolves inside it.
4. Use only `policy="now"`, `"end"`, or `"live"`.
5. Avoid `s3://` or `gs://` values as `glob_str`; they are rejected by base tracking save validation.
6. In disabled mode, do not expect filesystem or upload side effects.

Example:

```python
matched = run.save("*.pt", base_path="checkpoints", policy="end")
if not matched:
    raise FileNotFoundError("No checkpoint files matched checkpoints/*.pt")
```

## `async_log` and process pitfalls

Use `async_log` only for functions that return dictionaries suitable for `log`.

Threading:

```python
swanlab.async_log(lambda: {"score": 0.9}, step=1, mode="threading")
```

Asyncio:

```python
async def compute():
    return {"score": 0.9}

# Must be called while an event loop is running.
swanlab.async_log(compute, step=1, mode="asyncio")
```

Spawn:

```python
def compute_score(x):
    return {"score": float(x)}

swanlab.async_log(compute_score, 3, step=3, mode="spawn")
```

Avoid:

- Local/nested functions with `spawn` when they cannot be pickled.
- Returning tensors, open files, locks, or media objects from spawned processes.
- Calling parent `run.log` inside a forked child.
- `mode="fork"`, which is currently not implemented.

If an async task raises, `finish()` should still complete, but that task does not log metrics. Inspect the task's future or application logs to diagnose the underlying exception.

## `define_scalar` is currently optional-only

Although `define_scalar` appears in the public API surface, current behavior is a `NotImplementedError`. If a user reports this error, the fix is to remove the required call or guard it:

```python
try:
    swanlab.define_scalar(key="train/loss", name="Training loss")
except NotImplementedError:
    pass
```

Continue logging scalars with `swanlab.log({"train/loss": value}, step=step)`.
