# Generic conversion troubleshooting

Use this matrix before changing an adapter or rerunning a task. The generic
route owns orchestration and safety symptoms; source layouts, source-specific
padding, and historical LeRobot formats belong to the sibling routes named in
[the route boundary](../SKILL.md).

## Install and import failures

| Symptom | Likely cause | Safe response |
|---|---|---|
| `ModuleNotFoundError: datatrove` while importing the generic package | The pipeline imports DataTrove at module scope, even for local execution. | Install a compatible base DataTrove release in the inspection/runtime environment. Do not infer that local mode removes this dependency. |
| Missing `LeRobotDataset` or `aggregate` symbols under `lerobot.datasets` | LeRobot API drift or a mismatched environment. | Probe the exact target imports and dataset creation/aggregation signatures before conversion. The repository's import surface may differ from newer nested module locations; do not silently edit around it. |
| `ModuleNotFoundError: ray` only for `executor="ray"` | Ray extra is not installed. | Use local mode for a safe smoke test, or install and verify the Ray/DataTrove extra before selecting Ray. Never make Ray a hidden local prerequisite. |
| Video writer/reader, codec, or ffmpeg errors | Video features need a compatible LeRobot video stack and readable source files. | Validate codec, dimensions, pixel format, and target package support with a tiny safe probe. Skip or quarantine corrupt source episodes; aggregation cannot repair them. |
| `pyarrow`, NumPy, or pandas errors during aggregate | Parquet or array representation is incompatible with the target environment. | Check versions and feature dtypes/shapes. Test the aggregate API on a tiny synthetic metadata fixture only; do not patch production metadata in place. |
| Hub authentication or permission failure | Credentials, namespace, visibility policy, or repository access is missing. | Turn off `push_to_hub`, validate the local aggregate, then authenticate and recheck the exact `hub_repo_id`. A local repo id is not a Hub authorization. |

The verified environment plan treats Ray/DataTrove extras and simulator stacks as
optional. A missing optional stack is an explicit gap, not evidence that the
whole operating route is broken.

## Task and configuration validation

### No tasks

An empty result from `load_tasks()` stops with:

```text
No conversion tasks found. Provide a non-empty tasks file or matching source files.
```

Check source discovery, filters, glob patterns, and task manifest paths. Do not
create an empty LeRobot dataset just to satisfy the pipeline. The safe checker
reproduces this gate without importing LeRobot.

### Invalid CPU count

`cpus_per_task < 1` stops with:

```text
--cpus-per-task must be >= 1
```

Use a positive integer. The generic pipeline derives local workers from
`cpu_count // cpus_per_task` only when `workers=-1`, with a minimum of one. A
large `cpus_per_task` can reduce concurrency but does not by itself guarantee
more memory per task; budget memory explicitly.

### Incompatible task records

Before scheduling, ensure every task has:

- a real `input_path` that the source-specific adapter can read;
- a unique disposable `output_path` under the run's temp root;
- a non-empty `local_repo_id` used only for local dataset construction; and
- a mapping `metadata` containing only stable adapter-owned values.

Ensure all tasks share the adapter's feature schema, FPS, robot type, and
writer compatibility. Do not use metadata to smuggle a second schema into one
aggregate. If a task has no saved episodes, its temp root is deleted and the
aggregate may fail because no roots remain.

### Frame and episode failures

- Missing `task` in frames causes task/language conditioning to be lost or can
  fail writer validation. Put the chosen instruction in every frame, not just
  the task record.
- Wrong image height/width/channel order, depth flag, or dtype is a schema
  error. Reject or transform explicitly in the source-specific adapter; never
  silently reshape.
- A one-shot episode iterator is consumed by `save_episode` before the default
  `len()` logging call. Materialize it or override `get_episode_length`.
- If `save_episode` returns `False`, log a concrete reason. If all episodes are
  skipped, expect the worker to remove that temporary task output.
- A custom `create_dataset` or `save_episode` must preserve the same local repo,
  root, feature, episode-finalization, and boolean skip semantics unless the
  whole adapter contract is intentionally versioned.

## CLI and API misuse

| Misuse | Result or risk | Correction |
|---|---|---|
| `executor="rayy"` or another spelling | `ValueError: Executor ... not supported`. | Use exactly `local` or `ray`; prefer local first. |
| `workers=0` or another invalid explicit worker count | May fail inside DataTrove because the generic pipeline passes explicit values through. | Reject values below one except `-1` in a preflight checker. Use a bounded count. |
| Assuming `tasks_per_job` changes local behavior | It is ignored by local executor configuration. | Tune `workers` and `cpus_per_task` for local; use `tasks_per_job` only with Ray. |
| Passing `--repo-id` and assuming it is always a Hub target | In the documented wrappers it can control the local aggregate id; upload still needs the push flag and a Hub id. | Distinguish `local_repo_id` from `hub_repo_id` and verify wrapper semantics. |
| Setting `debug=True` but expecting all tasks or a Hub upload | Debug truncates to first two tasks, forces local/one worker, and disables push. | Use debug only as a bounded smoke test, then run a reviewed full plan. |
| Reusing `resume_dir` after changing task order, paths, features, or adapter code | Logs may no longer describe the data plan and can cause skipped or repeated work. | Start a new log directory or prove exact run identity. |
| Passing a resume log as `output_path` | The log directory is not a dataset root. | Keep `resume_dir`, final output, temp root, and raw source roots separate. |
| Setting `push_to_hub=True` without `hub_repo_id` | `ValueError` after local work. | Supply and review the exact destination, or leave push disabled. |

## Destructive path and cleanup failures

The pipeline deletes an existing task output when that task starts, deletes an
existing final output before aggregation, and by default removes the adapter's
sibling temp root afterward. This is intentional behavior, not a recoverable
backup mechanism.

For an existing dataset or an unrelated output at risk:

1. Stop before starting the executor.
2. Resolve and compare final, temp, task, raw, and resume paths.
3. Move the intended result to a new output name or obtain explicit approval
   for replacement; the generic pipeline has no dry-run or backup flag.
4. Set `cleanup_temp=False` only when preserving run-owned temp data for
   inspection, and delete it after review. It does not protect paths outside
   `adapter.temp_output_path`.
5. If aggregation fails after deleting the old final root, recover from a
   separately maintained backup or rebuild from surviving temp roots; do not
   assume resume logs can restore it.

A multi-task adapter with a resume directory is especially sensitive: a stale
log can coexist with a newly generated task list, while aggregation still
removes the final output. The safe planning recipe in
[pipeline behavior](pipeline-behavior.md) is the required difficult-case
procedure.

## Aggregation, arrays, and videos

- `No temporary datasets were produced; nothing to aggregate.` means all tasks
  failed, were skipped, or their roots were removed. Inspect task logs and
  preserve temp output on the next controlled attempt.
- Nested NumPy arrays may fail parquet writes or produce inconsistent schemas.
  The aggregate shim normalizes multidimensional arrays observed in a bounded
  sample to nested lists, but it is not a substitute for consistent adapter
  output. Validate every episode's shapes.
- Video keys must be consistent across tasks. A missing or corrupt file, codec
  mismatch, dimension mismatch, or bad timestamp can break copy/concatenation.
  Quarantine the offending task or disable that modality in the declared
  schema; do not claim a successful video aggregate when only metadata moved.
- If the target LeRobot release changed aggregate helper signatures or metadata
  columns, the compatibility shim may fail. Pin/recreate a compatible
  environment and re-run a safe import/signature probe rather than modifying
  the pipeline in place.

## Source-specific boundary and escalation

If the failing symptom is a raw directory, HDF5 key, RLDS transform, embodiment
mapping, simulator regeneration, or version layout issue, stop editing the
generic adapter and route to the appropriate sibling: `openx-conversion`,
`agibot-conversion`, `robomind-conversion`, `libero-conversion`,
`robocasa-conversion`, `rlds-export`, or `version-migration`. Generic
aggregation should receive already normalized episodes and should not encode
those layouts.

## Safe checks

The bundled checker accepts a JSON contract manifest and performs only parsing
and validation. It does not import the adapter, create directories, read raw
data, invoke DataTrove/Ray, write parquet/video files, or contact the Hub. Use
it for empty-task, CPU, path-uniqueness, required-attribute, and push-argument
checks before a real run. The runtime skill's own construction checks likewise
remain static/synthetic; full conversions and cluster operations are outside
this route's safe boundary.
