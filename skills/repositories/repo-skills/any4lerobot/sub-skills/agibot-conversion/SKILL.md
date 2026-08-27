---
name: "agibot-conversion"
description: "Routes AgiBotWorld raw-tree conversion requests to LeRobot,
  covering end-effector selection, task filtering, episode alignment, depth and
  video handling, execution controls, and recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# AgiBotWorld conversion

Use this route when a user needs to convert an AgiBotWorld/AgiBot-World raw
release into a LeRobot dataset, select gripper/dexhand/tactile tasks, preserve
AgiBot state and action names, or diagnose an AgiBot conversion failure. This
route is dataset-specific. Load [`generic-conversion`](../generic-conversion/SKILL.md)
for shared adapter lifecycle, temporary aggregation, local/Ray executor
semantics, resume logs, cleanup, and Hub publication; do not duplicate that
pipeline here.

## Safety and compatibility boundary

- Treat the raw tree and the output root as separate resources. Inventory both
  before scheduling work, and never use the source tree as an output root.
- Prefer a read-only structural preflight, `--executor local`, and `--debug`
  for the first run. The default executor is Ray, but Ray is optional for a
  single-node conversion.
- Do not enable `--push-to-hub` until the local dataset opens and its task,
  episode, feature, and modality counts have been reviewed. Require an
  explicit `--repo-id` and confirm the destination is not an unintended
  existing dataset.
- The AgiBot implementation uses a custom metadata flush and dataset writer.
  It is version-sensitive and must be checked against the installed LeRobot
  API before conversion. In the verified environment, current LeRobot exposes
  `LeRobotDataset` and `LeRobotDatasetMetadata` under
  `lerobot.datasets.lerobot_dataset`, while the source import style also
  expects exports from `lerobot.datasets` and `lerobot.datasets.dataset_writer`.
  Treat an import-layout mismatch as a blocking compatibility issue, not as a
  reason to edit metadata by guesswork.
- Do not run a conversion, Ray cluster, video decode, download, or Hub push
  while only planning or validating this route.

## Route checklist

1. Confirm the release root contains `task_info/`, `observations/`, and
   `proprio_stats/`; confirm that the requested task IDs and episode IDs are
   present in the release rather than inferred from a filename alone.
2. Choose exactly one `--eef-type`: `gripper`, `dexhand`, or `tactile`. Keep
   task families separate. The gripper route means the tasks not reserved for
   dexhand or tactile in the built-in mapping; it is not a universal “all
   tasks” switch.
3. Check the selected task JSON records, HDF5 state/action paths, every required
   RGB/tactile video, and depth frame count when `--save-depth` is requested.
   Use the schemas in [data formats](references/data-formats.md).
4. Decide task granularity with `--episodes-per-task`. Use `1` for load
   balancing and isolation, or a larger value when task-start overhead and
   memory are acceptable. Chunk names are deterministic but are not semantic
   task IDs.
5. Select execution and resource flags from [workflows](references/workflows.md),
   including `--executor`, `--cpus-per-task`, `--tasks-per-job`, `--workers`,
   `--resume-dir`, and `--debug`. Start locally; only use Ray after cluster
   ownership, shared paths, optional dependencies, and worker memory have been
   confirmed. Budget roughly 20 GiB per active task and about 3 CPU cores per
   task as a starting point, then reduce concurrency if memory is constrained.
6. Preserve the frame task label (`task_name | init_scene_text`) and the
   per-episode `action_config`. Do not flatten or rename nested state/action
   keys without recording an explicit downstream schema change.
7. Interpret failures conservatively: missing video is skipped before loading,
   corrupt video is skipped when episode saving fails, action longer than state
   skips the episode, and depth count mismatch must be investigated rather than
   padded silently. See [troubleshooting](references/troubleshooting.md).
8. Validate the local result before resume or publication: feature names and
   shapes, task labels, action metadata, episode counts, depth presence, video
   readability, and absence of unexpected temporary output. Then hand shared
   cleanup, aggregation, resume, and Hub behavior to `generic-conversion`.

## AgiBot-specific transformation

The converter reads state and action arrays from `proprio_stats.h5`, emits one
frame per state sample, and attaches the natural-language task label to every
frame. Empty action arrays become zero-valued frames of the configured shape.
Short action arrays are reconstructed from the corresponding state stream and
placed at the recorded action indices when those indices exist; an empty
`action/.../index` may fall back to the joint index. An action stream longer
than the state stream is treated as corrupt and the episode is skipped. This is
alignment policy, not generic padding and must be recorded in provenance.

RGB and tactile streams remain video features; optional head depth is loaded as
float32 image data from depth frames and scaled from millimetres to metres. The
custom writer stores task indices, action configuration, episode statistics,
and video references while writing episode metadata as Parquet. These details
are summarized, with no source-code dependency, in the bundled references.

## Difficult synthetic case

For a mixed raw tree containing one gripper task, one dexhand task, and one
short-action episode, first filter by `--eef-type` and explicit `--task-ids`,
then verify that the short action is reconstructed only when the index/state
contract is valid. Add a task with a missing depth frame and another with a
missing or corrupt video: the video case should be skipped with a reason; the
depth case should stop or be excluded by preflight rather than silently
inventing frames. This case is suitable for an integration usability test and
requires no real AgiBot data.

## Handoff and evidence

Report the source release shape, selected end-effector and tasks, skipped
episodes with reasons, alignment and depth decisions, execution/resource
flags, compatibility checks, output validation, and any unresolved optional
backend gap. Evidence for this route was distilled from the repository README,
the AgiBot conversion README, `agibot_h5.py`, `agibot_utils/agibot_utils.py`,
`agibot_utils/config.py`, and `agibot_utils/lerobot_utils.py`; these artifact
names are provenance only and are not runtime dependencies.
