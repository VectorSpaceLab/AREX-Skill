# AgiBotWorld troubleshooting

Use the symptom, cause, and safe response together. Preserve the source,
preflight report, logs, and partial-output inventory; do not “repair” a dataset
by deleting files until the affected root is known to be disposable.

## Install and import failures

| Symptom | Likely cause | Safe response |
|---|---|---|
| `No module named h5py` | Raw proprioception is HDF5 and the base install is incomplete | Install `h5py` in the selected environment, then run a read-only import probe |
| `No module named pyarrow` or Parquet errors | Metadata flush needs PyArrow | Install a compatible PyArrow version and verify a tiny in-memory table before conversion |
| `No module named torchcodec` or video decoder failure | Episode statistics sample video frames through TorchCodec | Install/verify TorchCodec and its FFmpeg/runtime support; do not replace video statistics with guessed arrays |
| `LeRobotDataset` import fails from `lerobot.datasets` | LeRobot export layout differs from the source import style | Check whether the symbols live under `lerobot.datasets.lerobot_dataset`; adapt only through a reviewed compatibility layer |
| `DatasetWriter` import or method-signature failure | The custom writer targets a different LeRobot release | Compare writer/create/save signatures and metadata methods; stop if the custom writer cannot be made compatible |
| stats validator rejects depth | Installed LeRobot applies a color-image shape rule to depth | Use a supported depth-aware stats implementation or disable depth explicitly; never bypass validation silently |
| Ray/DataTrove import fails | Distributed executor extras are absent | Use `--executor local` for the baseline, or install and verify the optional Ray/DataTrove stack before distributed work |

The selected environment is expected to provide Python, NumPy, HDF5, PyArrow,
Pillow, Torch, and TorchCodec for the core route. Ray/DataTrove are optional
for distributed execution. CUDA is not required for the route, although video
libraries may use available acceleration. An import check does not prove that
a raw dataset can be converted.

## Input and configuration validation

### No tasks are scheduled

Check all of the following without writing output:

- `task_info` exists and contains JSON files named with the expected task ID
  convention;
- the requested IDs include the `task_` prefix used by task JSON stems;
- the numeric task directory matches the final filename token;
- `--eef-type` matches the intended family;
- the selected IDs are not reserved for a different family; and
- task JSON records contain numeric `episode_id` values.

An empty task list is not proof that the raw release is empty. It may indicate
that a gripper request selected a dexhand/tactile task or that an ID was typed
in the wrong form.

### Task metadata or HDF5 keys are missing

The route needs `task_name`, `init_scene_text`, `episode_id`, and
`label_info.action_config` to preserve task and episode metadata. For each
selected episode, verify `proprio_stats/<id>/<episode>/proprio_stats.h5` and all
configured `state/<name>` and `action/<name>` datasets. A similarly named HDF5
key is not an acceptable substitute: the end-effector configuration controls
both semantic names and expected shapes.

### State streams have inconsistent lengths

Use the first state stream's length as the candidate frame count and compare all
other selected state arrays. Do not let one short state silently truncate the
episode. If the arrays disagree, classify the episode as invalid unless a
reviewed release-specific alignment rule exists.

### Action length is short, empty, or too long

An empty action is intentionally represented by zero vectors with the configured
shape. A shorter action can be reconstructed from the corresponding state
array only when the action index dataset is present and valid; an empty end
index may use a joint index fallback. Verify index bounds and the resulting
shape before accepting it. An action longer than the state stream is a known
dirty-data pattern and must be skipped, not truncated.

### Depth is missing or misaligned

Without `--save-depth`, depth is not part of the selected feature schema. With
it enabled, verify that the depth directory exists, that `head_depth*` files
are decodable, and that their count equals the state frame count. The loader
raises on a count mismatch; missing depth therefore needs a preflight exclusion
or an explicit repair decision. Do not pad with the last frame or zeros unless
the downstream dataset contract explicitly permits that transformation and the
change is recorded.

## Video and episode-save failures

### A required video does not exist

The preflight should derive standard RGB paths from the configured camera names
and tactile paths from the sensor names. Missing files are rejected before
loading and the episode is skipped. Record task ID, episode ID, and the missing
paths. Do not create empty MP4 placeholders: the output would claim a modality
that is not present.

### An MP4 exists but is corrupt

The writer may accept the path initially and fail while saving or computing
video statistics. The route catches that episode-level save failure, reports a
corrupt MP4, clears the in-memory episode buffer, and continues. Check the
logs and output task-local directory for remnants, then confirm the final
episode count reflects the skip. A corrupt video in one camera invalidates the
whole episode because all configured video keys are part of the feature schema.

### Video dimensions or codecs disagree

Inspect representative decoded frames and the metadata declaration before
retrying. The route declares fixed camera shapes and uses TorchCodec sampling
for episode statistics. Do not silently resize, swap RGB/BGR order, or change a
feature from video to image to make validation pass; make a reviewed schema
change instead.

## CLI and API misuse

- `--episodes-per-task` must be at least 1. Use `1` when isolating a failure;
  larger values only change scheduling granularity, not semantic episode IDs.
- `--task-ids` takes one or more values after the flag. Use the task stem form
  expected by `task_info`, not only the numeric directory token.
- `--executor` accepts `local` or `ray`. Do not pass a Ray-only
  `--tasks-per-job` expectation to local mode; it has no effect there.
- Use a positive, explicitly chosen `--workers` value when diagnosing memory
  pressure. The `-1` default may start more concurrent work than the host can
  hold.
- `--save-depth` changes the feature schema and validation requirements; it is
  not a post-processing toggle.
- Treat `--repo-id` as mandatory with `--push-to-hub`, even if parser versions
  do not enforce the relationship. Confirm authentication and destination
  ownership separately from conversion correctness.
- Do not use `--resume-dir` with changed task family, source release, feature
  schema, or output root. Start a new run directory for a changed plan.

## Memory, CPU, Ray, and resume failures

The repository guidance estimates about 20 GiB of memory per conversion task
and recommends around three CPU cores per task. If workers are killed, the
process is swapped, or video decoding stalls, reduce `--workers`, set
`--episodes-per-task 1`, reduce Ray task concurrency, and keep the run local
until a stable baseline exists. Adding CPUs without reducing concurrency does
not necessarily reduce total memory.

For Ray failures, distinguish a missing optional dependency, a worker that
cannot see the source/output filesystem, an exhausted object store, and an
unowned/stale cluster. Confirm the cluster address and shared paths before
retrying. A local successful episode is the CPU substitute for executor
semantics; it is not evidence that a multi-node cluster is configured.

For resume failures, verify that the log directory was produced by the same
source snapshot and flag set, and that its temporary outputs were not manually
moved. If the output is ambiguous or partially aggregated, preserve it and
start a new disposable output rather than asking resume to reinterpret it.

## Custom metadata and output corruption

The AgiBot writer extends LeRobot metadata handling to serialize buffered NumPy
values for Parquet and attaches `action_config` to each episode. It also
replaces the normal dataset metadata/writer objects during creation. Symptoms
such as missing `meta/episodes`, task-index errors, inconsistent Parquet
schemas, or missing action configuration usually indicate an installed
LeRobot/custom-writer mismatch or an interrupted task-local write.

Stop and inspect the output metadata, Parquet schema, and logs. Do not copy a
writer class from an older checkout into a new environment without reviewing
its APIs. If the custom writer cannot be reconciled with the installed
LeRobot version, report the compatibility block and leave the source untouched.

## Hub and cleanup failures

A failed Hub upload does not prove that local conversion failed. Validate and
retain the local root first, then retry publication separately with the same
metadata and explicit destination. Never use a publish retry as a conversion
resume unless the shared pipeline documents that behavior.

Temporary per-task datasets are disposable only after the final aggregation,
skip report, and output validation are complete. If cleanup fails, list the
contents and ownership of the temporary root; delete only the root created for
this run. Never apply broad recursive deletion to a parent directory that may
contain another dataset or a raw release.

## Known dirty-data cases

The documented AgiBot dirty-task set includes action-longer-than-state
episodes for `task_352`, `task_354`, `task_359`, `task_361`, `task_368`,
`task_376`, `task_377`, `task_410`, `task_414`, `task_421`, and `task_711`,
and corrupted MP4s for `task_380`, `task_384`, `task_428`, `task_460`,
`task_505`, and `task_510`. Treat the list as a warning, not as a complete
quarantine list: new releases may contain additional failures. Keep a
machine-readable skip report with task ID, episode ID, category, and exception
summary so a later run can distinguish intentional filtering from data loss.
