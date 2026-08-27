# Experiment Tracking API Reference

This reference targets W&B SDK version `0.27.3.dev1` and Python `>=3.10`.

## Core entry points

### `wandb.init(...) -> Run`

Important parameters:

- `entity`, `project`: destination account/team and project.
- `dir`: root directory for local experiment logs and metadata; defaults to a local W&B directory under the working tree.
- `id`: stable run identifier for resume/fork workflows. It must not contain `/`, `\`, `#`, `?`, `%`, or `:`.
- `name`, `notes`, `tags`, `group`, `job_type`: UI organization metadata.
- `config`: dictionary, namespace/flags object, or YAML path containing run inputs and hyperparameters.
- `mode`: one of `"online"`, `"offline"`, `"disabled"`, or experimental `"shared"`.
- `force`: require login instead of falling back when credentials are missing.
- `reinit`: active-run behavior; accepts `None`, booleans, `"default"`, `"return_previous"`, `"finish_previous"`, or `"create_new"`.
- `resume`: `"allow"`, `"never"`, `"must"`, or `"auto"`; ignored in offline mode.
- `resume_from`, `fork_from`: beta run-history controls, mutually exclusive with `resume`.
- `settings`: `wandb.Settings` or a dictionary for advanced behavior.

`wandb.init()` starts a background service, returns a `Run`, and syncs online by default. Prefer a context manager so `Run.finish()` is automatic. If a run is already active, the SDK consults `reinit`: it may finish previous runs, create a new run, return the previous run, or raise for incompatible resume behavior.

### `wandb.login(...) -> bool`

Programmatic counterpart to the login CLI. It can read credentials from an explicit key, `WANDB_API_KEY`, settings, netrc, or an interactive prompt. Do not hard-code API keys in generated examples. Offline and disabled tracking do not require login.

### `wandb.finish(exit_code=None, quiet=None)` and `Run.finish(...)`

Finish uploads or finalizes remaining data and marks the run state. `exit_code=0` means success; nonzero marks failure. The `quiet` argument is deprecated in favor of `wandb.Settings(quiet=...)`.

## `Run.log(data, step=None, commit=None)`

`Run.log()` accepts dictionaries with string keys and serializable values: numbers, strings, lists/tuples/NumPy arrays of serializable values, nested dictionaries, W&B data types, and media objects.

Rules and best practices:

- Keys must be strings. Non-dict payloads and non-string keys are errors.
- A slash groups metrics in the UI. Only one grouping level is meaningful; `a/b/c` groups under `a`.
- Each call creates a new implicit W&B step unless `commit=False` is used.
- Explicit `step` values must always increase; logging to a previous step is not supported.
- `commit=False` accumulates data for a step. A later committing call finalizes that step.
- Logging more than a few times per second can hurt performance. Batch or throttle high-frequency metrics.
- For custom x-axes, log an axis metric such as `epoch` or `train_step` and bind dependent metrics with `Run.define_metric()`.

```python
run.log({"loss": 0.5}, commit=False)
run.log({"accuracy": 0.8})

run.log({"epoch": epoch, "train/loss": loss, "val/accuracy": accuracy})
```

## `Run.define_metric(...)`

Signature highlights:

```python
run.define_metric(
    name,
    step_metric=None,
    step_sync=None,
    hidden=None,
    summary=None,
    goal=None,
    overwrite=None,
)
```

Use it to customize charts and summaries:

- `name`: metric name or suffix glob such as `train/*`. Glob stars are only supported as the final suffix.
- `step_metric`: another metric to use as the x-axis.
- `step_sync`: automatically inject the last `step_metric` value when omitted; defaults to true when `step_metric` is set.
- `hidden`: hide from automatic plots.
- `summary`: accepted aggregations include `min`, `max`, `mean`, `last`, `first`, `best`, `copy`, and `none`; prefer `min` or `max` over deprecated `best`/`goal` usage.
- `overwrite`: control whether repeated definitions merge or replace previous settings.

Invalid argument types, empty names, unsupported summary operations, or interior glob stars raise W&B errors.

## Config, settings, and run directories

`wandb.Settings` fields commonly useful for agents:

- `mode`: `online`, `offline`, `disabled`, `shared`, legacy `dryrun`, or legacy `run`.
- `init_timeout`: seconds to wait for initialization.
- `console`: `auto`, `off`, `wrap`, `redirect`, `wrap_raw`, or `wrap_emu`.
- `root_dir`: base directory used for local run files.
- `run_id`: lower-level run ID setting corresponding to `id`.
- `resume`: resume behavior.

For temporary or CI-safe tracking, pass `dir=temp_dir` to `wandb.init()` and set `mode="offline"` or `mode="disabled"`. Offline run folders are named like `offline-run-...-RUN_ID` and contain the local `.wandb` payload needed for later upload.

## Tables

`wandb.Table(columns=None, data=None, rows=None, dataframe=None, dtype=None, optional=True, allow_mixed_types=False, log_mode="IMMUTABLE")`

- Default columns are `Input`, `Output`, and `Expected` when no columns are provided.
- `data` should be row-oriented lists, NumPy arrays, or pandas DataFrames; with `dataframe=...`, DataFrame columns are used.
- Column names must be strings or integers.
- Default `log_mode="IMMUTABLE"` means a table is intended to be logged once. `MUTABLE` and `INCREMENTAL` are advanced modes for repeated or incremental table logging.
- Tables can contain scalars, strings, arrays, and many W&B media types.

## Media and plots

Common constructors:

- `wandb.Image(data_or_path, caption=..., normalize=True)`: accepts NumPy arrays, PyTorch tensors, PIL images, or image paths. Arrays/tensors may be normalized to `[0, 255]`.
- `wandb.plot.line_series(xs, ys, keys=None, title="", xname="x", split_table=False)`: creates a custom chart logged via `run.log()`.
- `wandb.plot.confusion_matrix(probs=None, y_true=None, preds=None, class_names=None, title="Confusion Matrix Curve", split_table=False)`: accepts either probabilities or predictions, not both, and requires compatible lengths.

Optional dependencies matter for rich media. If a dependency is unavailable, switch to scalar summaries or a `wandb.Table` and document the skipped media logging.

## Modes

- `online`: default live syncing. Requires network and credentials for authenticated projects.
- `offline`: writes complete local run data without network. `resume` is ignored in offline mode.
- `disabled`: methods become no-op-like and do not perform normal tracking side effects.
- `shared`: experimental multi-process logging to the same run ID; use only when the task explicitly needs shared runs.

## Error classes to expect

Instrumentation code should be prepared for `wandb.Error`, `AuthenticationError`, `CommError`, `UsageError`, and `KeyboardInterrupt` around initialization. For normal training scripts, let these fail loudly unless the user explicitly asks for optional telemetry fallback.
