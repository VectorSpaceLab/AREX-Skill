---
name: dataset-workflows
description: "Inspect, validate, create, load, stream, transform, visualize, and
  safely plan operations on LeRobot Dataset v3 repositories."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dataset workflows

Use this skill when the request mentions `LeRobotDataset`, `LeRobotDatasetMetadata`, a
LeRobot dataset root or repository, episodes, feature schemas, Parquet, MP4, image
transforms, statistics, streaming, porting, `lerobot-edit-dataset`,
`lerobot-dataset-viz`, `lerobot-imgtransform-viz`, or `lerobot-convert-dcp`.
This skill covers dataset storage and read/write planning. Route policy, training,
evaluation, and inference to `policy-training-inference`; route physical recording,
replay, cameras, robots, and teleoperators to `robot-control-data-collection`; route
Hub jobs, credentials, uploads, and other remote services to
`extensions-and-services`.

## Boundary and safety

- Inspect before mutating. Dataset editing, conversion, re-encoding, stats writes,
  Hub access, downloads, uploads, and credential use are side effects. The default
  plan is local, bounded, and non-destructive.
- A local dataset is the exact directory containing `meta/`, `data/`, and, for
  video features, `videos/`. Pass it explicitly as `root`; preflight
  `meta/info.json` and data shards before constructing a reader so a malformed
  local fixture cannot silently trigger a Hub download.
- Never infer video readiness from a successful import. Check the declared video
  keys, referenced MP4 paths, decoder backend, and a bounded sample decode.
- Do not call `push_to_hub`, `modify_tasks`, or an in-place edit without explicit
  user consent, an output/overwrite decision, and a rollback or backup plan.
- `finalize()` is mandatory after recording or conversion before reading or
  pushing. A missing Parquet footer can make an apparently complete dataset
  unreadable.

## Inputs and outputs

Collect the LeRobot version, source kind (local fixture, local full dataset, Hub
repo, or Storage Bucket), exact root/repo/revision, intended episodes, feature keys
and shapes, FPS, image/video/depth status, decoder choice, transforms, statistics
provenance, operation/output directory, overwrite intent, optional extras, and
network/credential consent. Produce one of:

1. a validated local load/stream plan and bounded sample report;
2. a schema, episode, feature, statistics, or decoder diagnosis;
3. a write/port/edit/convert plan with explicit output and validation gates; or
4. a blocked report naming the missing evidence or optional dependency.

Load the detailed contracts from [data-formats.md](references/data-formats.md),
[api-reference.md](references/api-reference.md), and
[workflows.md](references/workflows.md). Use [cli-reference.md](references/cli-reference.md)
for commands and [troubleshooting.md](references/troubleshooting.md) for recovery.
The bundled read-only helpers are [load_local_dataset.py](scripts/load_local_dataset.py),
[transform_probe.py](scripts/transform_probe.py), and
[dataset_operation_plan.py](scripts/dataset_operation_plan.py).

## Fast decision workflow

1. **Classify the source.** For a local fixture, require an existing root and do not
   download. For a Hub dataset, decide whether metadata-only, cached full access,
   or streaming is wanted. Storage Buckets require `repo_type="bucket"` and
   streaming; non-streaming `LeRobotDataset` cannot consume bucket data.
2. **Preflight the layout.** Confirm `meta/info.json`, `meta/stats.json` when
   normalization is needed, `meta/tasks.parquet` when tasks exist,
   `meta/episodes/*/*.parquet`, `data/*/*.parquet`, and the MP4 files named by
   episode metadata for every video feature. Check that the declared v3 version,
   FPS, paths, and counts agree.
3. **Validate schema and episodes.** Compare Parquet columns to `info.features`;
   verify numeric dtype/shape, image shape/order, task indices, contiguous episode
   ranges, `dataset_from_index`/`dataset_to_index`, and `length`. Missing or
   malformed episode index is a metadata/data contract failure, not a reason to
   guess a repair.
4. **Choose reader.** Use `LeRobotDataset(repo_id, root=...)` for random access and
   `DataLoader`; select `episodes`, `episode_filter`, `delta_timestamps`,
   `image_transforms`, `return_uint8`, `video_backend`, or depth output deliberately.
   Use `StreamingLeRobotDataset` for bounded Hub/bucket iteration, shuffling, and
   delta windows; it is an `IterableDataset`, not an indexable random-access set.
5. **Probe a sample.** Check returned keys, tensor shapes/dtypes/ranges, episode
   boundaries, task text, and video decoding. A delta window is padded at an
   episode edge and emits `<feature>_is_pad`; offsets must be multiples of `1/fps`
   within tolerance.
6. **Plan mutations.** Name a distinct output root/repo, check it is absent or ask
   for overwrite, estimate disk/time, and validate feature compatibility before
   delete/split/merge/feature edits/conversion/re-encoding/stats recomputation.
   `modify_tasks` is in-place in the current tool contract. Prefer dry-run helper
   output before `lerobot-edit-dataset`.
7. **Handoff.** State exactly what passed, what was not tested (especially codecs,
   remote access, or optional viz), and which downstream skill owns the next step.

## Creation and write gates

Create with `LeRobotDataset.create(repo_id, fps, features, root=..., use_videos=...)`.
Feature entries need `dtype` and `shape`; numeric values must match NumPy dtype and
shape, image/video frames accept HWC or CHW arrays (or PIL), and every frame needs a
`task`. Recording code adds the standard `timestamp`, `frame_index`,
`episode_index`, `index`, and `task_index` features. Call `add_frame` repeatedly,
`save_episode`, then `finalize`; only after that call `__getitem__`, compute/verify
stats, or push. Use `resume` only with an explicit writable root.

Video storage uses MP4 per camera stream; image storage embeds image data in
Parquet. RGB encoding is PyAV-backed and needs the dataset/AV extra plus a codec
available in the FFmpeg/PyAV build. Depth video is a separate quantized 12-bit
stream with persisted depth parameters; decode to `mm` or `m` explicitly. An
image-only dataset is a valid CPU fallback, but it does not prove MP4 support.

## Validation checklist

- Local preflight found all required metadata/data paths without network access.
- `info.codebase_version` is v3-compatible; feature keys, dtypes, shapes, FPS, and
  task/episode counts agree with Parquet.
- Every requested episode is present; each frame range and referenced video range
  matches its declared length.
- Stats are present and shape-compatible with the features, or their absence is
  explicitly accepted by the downstream consumer.
- One bounded item or stream sample has expected tensors and task text; delta
  padding behavior is understood.
- Video backend and optional packages are proven separately from imports; codec
  failures are reported as unsupported/corrupt rather than worked around silently.
- Any edit has a distinct output or explicit overwrite/backup approval, and no Hub
  or long conversion was started during inspection.
