# Generic pipeline behavior

This is a behavioral model of `run_converter` and its task worker. It is
intentionally a compact distillation rather than a copy of the pipeline
implementation. It is derived from the repository's generic pipeline module
and the local/Ray usage documented for AgiBot and LIBERO.

## Inputs to `run_converter`

| Parameter | Meaning and safe use |
|---|---|
| `adapter` | A fully configured `BaseAdapter` instance. Its `output_path` is the final aggregate root. |
| `executor` | Exactly `"local"` or `"ray"`. Start with local. Any other value raises `ValueError`. |
| `cpus_per_task` | Must be at least 1. It controls Ray allocation and local worker derivation. |
| `tasks_per_job` | DataTrove Ray job packing value. It is passed to the Ray executor and has no local scheduling effect. |
| `workers` | Local worker count, or `-1` for `max(1, cpu_count // cpus_per_task)`; Ray receives the value as configured. Use a bounded positive number for memory-heavy work. |
| `resume_dir` | DataTrove logging directory. It is used as `logging_dir`; it is not a final dataset path or a replacement for a task manifest. |
| `debug` | Forces local/one-worker execution, limits tasks to the first two, and disables Hub upload. |
| `local_repo_id` | Repo id used for the final local aggregate metadata. It is separate from `hub_repo_id`. |
| `hub_repo_id` | Destination id used only when `push_to_hub=True`. |
| `push_to_hub` | Requests the final upload. It is forcibly disabled in debug mode and requires `hub_repo_id` otherwise. |
| `cleanup_temp` | Defaults to true; removes the adapter's sibling temp root after aggregation. Set false only for deliberate inspection. |
| `extra_tags` | Additional Hub tags, deduplicated after the built-in and adapter tags. |

The repository's dataset-specific command-line wrappers expose these concepts
with flags such as `--executor`, `--cpus-per-task`, `--tasks-per-job`,
`--workers`, `--resume-dir`, `--debug`, `--repo-id`, and `--push-to-hub`.
Wrappers may add source-specific flags; those belong to their sibling routes.

## Execution order and gates

The driver follows this order:

1. Call `adapter.load_tasks()`.
2. Reject an empty list.
3. Reject `cpus_per_task < 1`.
4. Create the final output parent.
5. Apply debug overrides, if requested.
6. Build the selected local or Ray DataTrove executor and logging directory.
7. Run one `SaveLeRobotDataset` pipeline step per task rank.
8. Aggregate surviving task roots into the final output.
9. Optionally delete the adapter temp root.
10. Optionally upload the aggregate to the Hub.

This order matters for synthetic checks: an empty task list is rejected before
debug truncation, and an invalid CPU count is rejected before any executor or
output work. The generic pipeline does not validate every worker or feature
value, so adapter-level preflight should be stricter than this minimum.

## Per-task worker lifecycle

Each worker selects its task by rank. If that task's output root already exists,
it is recursively deleted before the task starts. The worker then:

1. Creates a temporary `LeRobotDataset` using the task repo id and adapter-wide
   FPS, robot type, and feature map.
2. Calls `adapter.load_subset(task)`.
3. Calls `save_episode` for each yielded episode and logs its index and reported
   length.
4. Calls `dataset.finalize()`.
5. Deletes the task root if zero episodes were saved.

Consequences:

- Task output roots must be unique and disposable. Do not put a permanent
  artifact or the final root in one.
- A skipped episode is not an error by itself, but the reason must be recorded
  by the adapter. A task with all episodes skipped is removed and cannot be
  aggregated.
- The default length hook requires `len(episode_data)` after saving. Materialize
  episodes or override the hook for one-shot iterables.
- A worker failure can leave partial task output. Resume logs and manual output
  inspection must distinguish partial data from a completed task.

## Local versus Ray

### Local

With `executor="local"`, the pipeline lazily imports DataTrove's local
executor. `workers=-1` resolves to the available CPU count divided by
`cpus_per_task`, with a minimum of one. An explicit worker value is passed
through, so reject zero or negative values other than `-1` in adapter-facing
validation. Local mode still needs the base DataTrove and LeRobot stacks; it
does not need Ray.

### Ray

With `executor="ray"`, the pipeline lazily imports Ray, its DataTrove executor,
and `RuntimeEnv`, then calls `ray.init`. It passes `workers`,
`cpus_per_task`, and `tasks_per_job` to DataTrove and supplies environment flags
for HDF5 file locking, Hugging Face progress bars, and SVT logging. It also
constructs a propagated Python path from the running process. Do not mistake
that convenience for a portable package deployment: every worker still needs
the same installed adapter, LeRobot version, raw-data visibility, codecs, and
permissions. Use an explicit cluster setup and shared storage policy outside
this route when required.

Ray is optional. A missing Ray import should block only the Ray branch, not a
local smoke test. Never start a cluster as part of a static contract check.

## Resume and debug semantics

A `resume_dir` becomes the executor's `logging_dir`, whether local or Ray. It
therefore must identify the same logical run: same adapter version, task order,
input paths, temporary output roots, feature schema, and relevant options.
Changing those while reusing logs can skip, repeat, or mix work. A resume
folder does not make a deleted final output safe, and it does not validate that
an existing temp root is complete.

`debug=True` is a deliberate safety override, not merely verbose logging. It
selects the first two tasks in the returned list, forces one local worker, and
sets `push_to_hub=False`. It does not guarantee that the first two tasks are
representative; choose or order tasks intentionally in the adapter manifest.

## Aggregation and normalized arrays

Before aggregation, the pipeline deletes an existing final output root. It then
collects only task roots that still exist; if none remain, it raises `ValueError`
with `No temporary datasets were produced; nothing to aggregate.`

The aggregate call is wrapped to normalize DataFrame values before reading and
writing parquet. The wrapper recursively turns multidimensional NumPy arrays
into nested Python lists, while one-dimensional arrays remain arrays. Detection
checks a bounded sample of the first rows, so an adapter must still enforce
consistent shapes across all episodes. Metadata index columns are remapped to
account for each source dataset's episode/frame offsets; data and video source
chunk/file mappings are preserved when present.

The wrapper temporarily replaces selected LeRobot aggregation helpers and
restores them in a `finally` block. This compatibility shim is intentionally
version-sensitive: if the target LeRobot aggregate module changes names,
arguments, parquet handling, or metadata columns, stop and revalidate rather
than patching a live run blindly.

## Video aggregation

For each video key, aggregation tracks source chunk/file pairs and destination
chunk/file pairs. It copies the first source file, then either starts another
destination file when concatenation is disabled or the size threshold is
reached, or concatenates compatible videos and records a duration offset.
Episode video timestamps are shifted by those offsets, and metadata indices are
updated. This assumes compatible codecs, dimensions, pixel formats, and readable
files. A corrupt or incompatible video should be rejected or skipped by the
source-specific adapter; aggregation is not a repair tool.

Video handling can be parallelized by key with a thread pool. It is still
I/O-, codec-, and memory-bound. Avoid interpreting multiple workers as a
promise of linear speedup.

## Cleanup and Hub boundary

When `cleanup_temp=True`, the pipeline recursively removes
`adapter.temp_output_path` after a successful aggregate call. Custom task roots
outside that sibling are not covered by this cleanup. Preserve temp data only
when investigating a failure, and remove it manually after confirming it is
owned by the run.

When Hub upload is requested, a missing `hub_repo_id` raises `ValueError`.
After aggregation, the pipeline constructs a LeRobot dataset rooted at the
local output and calls the target release's Hub upload with public visibility,
video upload enabled, the Apache-2.0 license, and large-folder upload disabled.
Tags are ordered unique values from `LeRobot`, `dataset_type`, `robot_type`,
adapter tags, and extra tags. Treat this as a side-effecting operation: verify
metadata, destination, authentication, visibility, and overwrite policy before
setting the flag.

## Safe planning recipe

For a multi-task adapter with a resume directory:

1. Produce and inspect a deterministic task manifest without writing dataset
   data. Confirm non-empty tasks, unique task output roots, source-root
   separation, and stable metadata.
2. Verify that the resume directory belongs to exactly that manifest and to the
   same adapter/schema/options revision.
3. Use a new, uniquely named final output unless an explicit destructive
   replacement has been approved. Remember that aggregation deletes the old
   final root before checking for surviving temp roots.
4. Run debug locally with Hub push disabled, inspect the aggregate and preserved
   temp outputs if needed, then choose bounded local workers for the full run.
5. Only after review decide whether to clean temp roots and whether to upload.

This recipe supports the difficult case without executing a conversion, Ray
job, video operation, or Hub write during skill construction.
