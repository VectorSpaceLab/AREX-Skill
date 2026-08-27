# Transformer Lab SDK Reference

This reference distills the Python SDK behavior needed to modify task-script APIs, resource abstractions, storage/organization context, and the remote command wrapper. It assumes the `transformerlab` package version `0.1.46`.

## Package shape and exports

The SDK package is imported as `lab`. Public exports include:

- `lab`: singleton `Lab()` facade for simple task scripts.
- `Lab`: facade class for explicit instances or tests.
- `Job`, `Experiment`, `Model`, `Dataset`, `Task`, and `TaskTemplate` resource classes.
- `JobStatus` and `TERMINAL_STATUSES`.
- Legacy constants `HOME_DIR` and `WORKSPACE_DIR`; prefer async directory helpers for current workspace resolution.

The package script `tfl-remote-trap` points to the remote wrapper described below.

Important CLI/SDK split: the CLI does not use this SDK directly. The SDK is for Python code running as local or remote Transformer Lab jobs and for backend/resource code that manipulates workspace state.

## Lab facade lifecycle

Verified signatures:

```python
Lab.init(self, experiment_id: str | None = None, config: Optional[Dict[str, Any]] = None) -> None
Lab.finish(
    self,
    message: str = "Job completed successfully",
    score: Optional[Dict[str, Any]] = None,
    additional_output_path: Optional[str] = None,
    plot_data_path: Optional[str] = None,
) -> None
```

Typical task script:

```python
from lab import lab

lab.init()
config = lab.get_config() or {}
lab.log(f"starting with {config}")
lab.update_progress(10, metrics={"loss": 1.2}, step=0)
# work ...
lab.save_artifact("summary.json", "summary.json")
lab.finish(message="done", score={"accuracy": 0.91})
```

Rules:

- Call `lab.init()` before `lab.log`, `lab.update_progress`, save helpers, `lab.finish`, or `lab.error`. The facade's guard raises if a method needs an initialized job.
- If `_TFL_JOB_ID` is set, `init()` attaches to that existing job. If not, it creates a job under the resolved experiment.
- Experiment resolution prefers the explicit argument, then `_TFL_EXPERIMENT_ID` or `TFL_EXPERIMENT_ID`, then `alpha`.
- On init, the job status becomes `RUNNING`, start time is filled when missing, `live_status` is best-effort set to `Lab initialized`, and optional tracking integrations are probed without being allowed to break core behavior.
- Passing `config` to `init()` merges it into job data. Without explicit config, `get_config()` reads launched task parameters from `job_data["parameters"]` and returns `{}` if absent.
- Sync facade methods call an internal async runner. Do not call sync methods from inside an already-running event loop; use the corresponding `async_*` method.

## Logging, progress, metrics, finish, and error

`lab.log(message)`:

- Writes task output through the job log path and also logs to the process logger.
- Coerces messages to strings and appends a newline.
- Uses append mode for local files and read-modify-write for remote storage where append may be inefficient.
- Best-effort captures W&B/Trackio metadata and never lets optional tracking failures break the task.

`lab.update_progress(progress, metrics=None, step=None)`:

- Updates the top-level job progress percent.
- If `metrics` is supplied, overwrites `job_data.current_metrics` with the latest metrics.
- Appends a JSONL row to the job's `metrics.jsonl` with timestamp, progress, optional step, and optional metrics.
- Live metrics are not final scores. Use `finish(score={...})` for final comparable metrics.

`lab.finish(...)`:

- Updates progress to `100`.
- Writes `completion_status="success"`, `completion_details`, `end_time`, and final `score` in one job-data update.
- Adds `discard=False` to the score dict unless the caller explicitly passes a `discard` value.
- Sets job status to `COMPLETE` after the completion fields are written.
- Optionally records `additional_output_path` and `plot_data_path` when non-empty.
- Copies profiling output when running under the remote wrapper and best-effort captures Trackio artifacts.

Score must be a dictionary of named metrics:

```python
lab.finish(score={"accuracy": 0.78})
lab.finish(score={"score": 0.78})
```

Do **not** pass a scalar such as `lab.finish(score=0.78)`. The current implementation only merges score values when `score` is a dict; scalar scores do not become usable `job_data.score` metrics.

`lab.error(message)`:

- Writes `completion_status="failed"`, `completion_details`, `end_time`, and failed status metadata.
- Sets job status to `FAILED`.
- Copies profiling output when available.

## Save helpers and job outputs

### `save_artifact`

`save_artifact(source_path, name=None, type=None, config=None)` stores outputs under the current job and returns the destination path.

Behavior by type:

- Default type: copy a file or directory into the job artifacts directory and append the destination path to `job_data.artifacts`.
- `type="dataset"`: accepts a DataFrame-like object with `to_json`, a Hugging Face dataset with `to_pandas`, or a path. It writes job-scoped dataset files and tracks `dataset_id` / `generated_datasets`.
- `type="model"`: writes a job-scoped model artifact and tracks model metadata. `save_model` is a convenience wrapper around this behavior.
- `type="evals"`: writes evaluation-result data and tracks `eval_results`.

For paths, local paths are resolved to absolute paths; remote paths and HTTP(S) paths are used as-is. Existence checks use local filesystem APIs for local paths and SDK storage APIs for remote paths.

### `save_dataset`

`save_dataset(df, dataset_id, additional_metadata=None, suffix=None, is_image=False, job_id=None)` writes a generated dataset under the job's datasets directory.

- If `job_id` is omitted and the facade has an initialized job, the current job id is used.
- The public dataset id is prefixed with the job id to avoid cross-job conflicts.
- Non-image datasets are written as JSON records inside a per-dataset directory.
- Image metadata-style datasets are written as `metadata.jsonl` under a per-dataset directory.
- Metadata is best-effort created/updated through the `Dataset` resource.
- Job data is updated with `dataset_id` and `generated_datasets`.

### `save_checkpoint`

`save_checkpoint(source_path, name=None)` copies a file or directory into the job's checkpoints directory and returns the destination path.

- Empty source path raises `ValueError`.
- Missing local or remote source raises `FileNotFoundError`.
- Directories overwrite an existing checkpoint directory of the same name.
- Job data tracks `checkpoints` and `latest_checkpoint`.

Resume helpers:

- `get_checkpoint_to_resume()` reads `parent_job_id` and `resumed_from_checkpoint` from job data and verifies that the parent checkpoint path exists.
- `get_parent_job_checkpoint_path(parent_job_id, checkpoint_name)` protects against escaping the checkpoint directory for both local and remote paths.

### `save_model`

`save_model(source_path, name=None, architecture=None, pipeline_tag=None, parent_model=None)` wraps `save_artifact(type="model")`.

- Optional metadata keys are passed through as model config.
- The model name is job-prefixed for uniqueness when saved through model artifact logic.
- For local development, if you modify SDK code, reinstall the SDK in editable mode and restart the API or worker process that imports it. The API imports the installed package, not a source tree by magic.

## Resource abstractions

### `Job`

A `Job` is backed by JSON under an experiment job directory.

Common operations:

- `Job.create(job_id, experiment_id)` / `Job.get(job_id, experiment_id)`.
- `get_dir()`, `get_log_path()`, `get_checkpoints_dir()`, `get_artifacts_dir()`, `get_profiling_dir()`.
- `update_progress(progress, metrics=None, step=None)` and metrics JSONL append.
- `update_status(status)`, `get_status()`, `get_progress()`.
- `get_job_data()`, `set_job_data()`, `update_job_data_fields(updates)`, `update_job_data_field(key, value=None, multiple=False)`.
- `log_info(message)` for task logs.
- `set_error_message`, `set_type`, sweep helpers, checkpoint/artifact path listing, and deletion.

`update_job_data_fields` is preferred for atomic multi-field updates. It requires a dict. Non-finite values are sanitized when writing job data so invalid JSON is not persisted.

### `Experiment`

An `Experiment` owns experiment metadata and job indexing.

Common operations:

- `create_or_get(experiment_id, create_new=False)`.
- `create_with_config`, `update_config_field`, `update_config`, `get_all`.
- `create_job(type="REMOTE")`.
- `get_jobs(type="", status="")`.
- Jobs index rebuild/update/remove helpers.
- `delete` and `delete_all_jobs`.

The cached jobs index is important for job listing performance. If a change writes job JSON directly, ensure the experiment index is updated or rebuilt through resource methods.

### `Task` and `TaskTemplate`

`Task` is the legacy/global task abstraction. `TaskTemplate` is experiment-aware and is what task command flows align with.

Key `TaskTemplate` behaviors:

- Task template directories are experiment-scoped.
- `create`, `get`, `set_metadata`, `get_metadata`, `list_all`, `list_by_type`, `list_by_experiment`, `list_by_type_in_experiment`, `list_by_subtype_in_experiment`, `get_by_id`, and `delete_all`.
- Listing helpers gather metadata defensively and sort task-like ids predictably.

### `Model` and `Dataset`

`Model` and `Dataset` support both global registry-style resources and job-scoped generated resources.

`Model`:

- `create`, `get`, `get_dir`, `set_metadata`, `get_metadata`, `list_all`.
- Import/detect helpers for model path metadata, architecture detection, checksums, provenance, and model JSON generation.

`Dataset`:

- `create`, `get`, `get_dir`, `set_metadata`, `get_metadata`, `list_all`.
- For job-scoped generated datasets, the job id participates in lookup and path resolution.

## Directory and organization context

The SDK uses context variables to keep team/organization storage separated.

Important functions:

- `set_organization_id(organization_id: str | None)` sets both the current org id and, where applicable, the current storage URI context.
- `get_organization_id()` returns the context value.
- `require_organization_id()` raises a clear runtime error when a path requires org context but none is set.
- `get_workspace_dir()` is the preferred async workspace resolver. `WORKSPACE_DIR` is a legacy placeholder.

Storage modes:

- Default/local single-tenant: workspace is under the product home directory.
- Explicit `TFL_WORKSPACE_DIR`: used when not overridden by remote/org-scoped storage context.
- `localfs` with `TFL_STORAGE_URI`: workspace is scoped as `TFL_STORAGE_URI/orgs/<org_id>/workspace`; root URI is `TFL_STORAGE_URI/orgs/<org_id>`.
- Remote storage with remote enabled: root is a per-team workspace URI such as an S3/GCS/Azure-style workspace root.
- `juicefs`: API-server context maps org ids to `s3://workspace-<org_id>` served by the configured gateway. Remote pods can rely on `TFL_STORAGE_URI` already being a team workspace URI.

When remote or multi-org storage is enabled and neither a context variable nor an already org-scoped environment URI is present, storage access raises `Organization context is required`. This is intentional; do not mask it with a fallback to a single global workspace.

Directory helpers create safe paths for experiments, jobs, tasks, artifacts, checkpoints, models, datasets, eval outputs, generation outputs, prompt templates, local provider roots, and local provider job directories. Prefer these helpers over hand-joining paths when code depends on workspace layout.

## Storage abstraction

The storage layer is an async facade over fsspec and local file operations.

Core helpers:

- `root_uri()`, `filesystem()`, `debug_info()`.
- `join`, `root_join`.
- `exists`, `isdir`, `isfile`, `makedirs`, `ls`, `find`, `walk`, `rm`, `rm_tree`.
- `open(path, mode="r", fs=None, uncached=False, **kwargs)` returning an async-compatible file wrapper.
- `copy_file`, `copy_dir`, and chunk helpers.

Remote path detection recognizes S3, GCS, and Azure-style URI prefixes. Local paths use a local fsspec filesystem. Remote storage options come from provider-specific environment variables, including AWS profile, GCP project, Azure connection/account options, or JuiceFS gateway options.

Operational implications:

- Missing or wrong credentials usually appear as fsspec filesystem construction, listing, open, or copy errors.
- Some remote filesystems do not support true append efficiently. The SDK often uses read-modify-write or sync filesystem wrappers to avoid async event loop and cache problems.
- For freshness-sensitive paths, use uncached filesystem helpers or resource methods that already request uncached reads.
- Keep storage URI/context debug data out of public runtime messages if it contains secrets, but use `debug_info()` during local diagnosis to verify provider, root, and filesystem type.

## `tfl-remote-trap` remote wrapper

`tfl-remote-trap` is the package entry point for `lab.remote_trap:main`. It wraps a remote job command and mirrors status/log information into job storage.

Invocation shape:

```bash
tfl-remote-trap -- python train.py --epochs 3
# equivalent module form:
python -m lab.remote_trap -- python train.py --epochs 3
```

Behavior:

1. Parses everything after `--` as the original command. Without a command it prints an error, marks live status as crashed when possible, and exits `1`.
2. Sets `job_data.live_status` to `Remote command started` when `_TFL_JOB_ID` is present.
3. Sets high-level job status to `RUNNING` unless the existing job is `INTERACTIVE`.
4. Runs the command in a shell with stdout and stderr merged.
5. Streams output to the console and periodically appends it to `provider_logs.txt` under the job directory.
6. On exit, overwrites `provider_logs.txt` with the full combined output for consumers expecting complete captured logs.
7. Handles SIGTERM/SIGINT by setting a live-status shutdown message and terminating the child process or process group.
8. If profiling is enabled, creates a temporary profiling area, injects optional torch profiler hooks, finalizes profiling, copies profiling output into the job profiling directory, and cleans up.
9. On success sets live status to `Remote command finished`; on nonzero exit sets live status to `Remote command crashed` and marks job status failed through the live-status helper.
10. Returns the wrapped command exit code.

All status/log/profiling writes are best effort. Failure to update live status or write provider logs should not change the wrapped command's exit code. When debugging remote jobs, distinguish:

- `provider_logs.txt`: stdout/stderr from the wrapped command and launcher context.
- task logs from `lab.log`: output written through the SDK's `Job.log_info` path.
- high-level job status: controlled by the wrapper and by `lab.finish()` / `lab.error()`.

## SDK test patterns

Use pytest with isolated workspace/storage environment and fresh imports when environment variables influence module import state.

Patterns to preserve:

- Create temporary home/workspace directories and set environment variables before importing SDK modules.
- Remove `lab.dirs` and `lab.storage` from `sys.modules` in tests that change storage-provider environment variables.
- Use `Lab()` instances in tests instead of relying on the singleton when state isolation matters.
- Assert `lab.finish(score={...})` writes `job_data.score` with the metric dict plus `discard` default.
- Assert save helpers create files and update job data lists.
- For storage-mode tests, assert localfs/remote/juicefs roots and that missing org context raises rather than falling back.
- For `Job.update_progress`, assert both latest `current_metrics` and appended metrics JSONL rows.
