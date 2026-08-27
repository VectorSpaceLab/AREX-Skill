# LIBERO troubleshooting

## Install and import

**`h5py` cannot be imported or a file will not open.** Install a compatible
Python/h5py pair in the intended environment and run a read-only `h5py.File`
open/close probe. Do not proceed with a partially installed environment.

**LeRobot imports fail or symbols moved.** The repository was written against a
particular LeRobot API shape, while current installations may place
`LeRobotDataset` and metadata classes under a different module than older
imports. Check the installed LeRobot version and the converter's import surface
before conversion. Pin or adapt the environment deliberately; do not patch a
successful import by adding checkout paths to `PYTHONPATH`.

**DataTrove/Ray is missing.** Use `--executor local`; Ray is optional for this
route. Install and verify the Ray extra only when distributed execution is
actually needed. A missing optional Ray dependency must not block a local
structural run.

**Video encoding fails.** Check the LeRobot writer's supported codecs,
ffmpeg/torchcodec availability, disk space, and image dtype/order. AV1 metadata
is documented for the canonical output but is not universally supported across
LeRobot versions. Fix the writer/environment contract rather than changing
feature shapes silently.

## Input and schema validation

**No tasks are discovered.** Confirm the path is a directory, the HDF5 files
are immediate children, and names end in `_demo.hdf5`. The loader skips names
that match neither `_SCENE<number>_<task>_demo.hdf5` nor `<task>_demo.hdf5`.
Print the skipped names and correct the selection or provide an explicit
filename-to-task mapping outside this route.

**`data` or an observation key is missing.** Stop. Do not interpret a different
HDF5 layout as LIBERO. Confirm each demo has `agentview_rgb`,
`eye_in_hand_rgb`, `ee_states`, `joint_states`, `gripper_states`, and
`actions` at the exact paths described in [data formats](data-formats.md).

**Frame counts disagree.** A demo with different `T` across images, state, or
action arrays is corrupt or uses a different contract. Quarantine it and
report the paths and lengths; do not truncate to the shortest array without an
approved data policy.

**The input is 128x128 but output expects 256x256.** This is an intentional
hard stop. Choose an explicitly 128-compatible feature schema or obtain
approval and prerequisites for external LIBERO regeneration at 256 resolution.
Never label a 128 array as 256 or rely on an unrecorded resize.

**Images have channels first, grayscale, BGR, or an unexpected dtype.** Stop
and document the adaptation. The route expects frame-major RGB `(T,H,W,3)`;
channel swaps and color conversions must be explicit and validated.

**The HDF5 has `states` but no required observation arrays.** `states` alone is
not sufficient for this converter. It may support simulator replay, but it
cannot replace the camera and proprioception keys.

**Actions are outside the expected range.** The converter clips only the last
action component before inversion and leaves the first six untouched. Report
out-of-range values, verify the source convention, and preserve the exact
transformation in provenance. Do not apply a second inversion.

## CLI/API misuse

**`--push-to-hub` was supplied without `--repo-id`.** Stop before writing or
uploading. Supply a valid namespace/name, authenticate separately, and review
local metadata first. `--repo-id` alone is not an upload request.

**`--debug` still appears to use Ray or upload.** Debug mode is expected to force
local behavior and disable Hub upload. Check the actual wrapper/entry point and
logs; do not assume a custom wrapper preserved the contract.

**`--tasks-per-job` appears ineffective.** It is a Ray scheduling control and
has no effect with `--executor local`. Adjust `--workers`/CPU settings for local
execution instead.

**Negative/zero worker or CPU settings cause odd scheduling.** Start with
`--cpus-per-task 1` and `--workers 1`. The documented `--workers -1` means the
executor default, not a promise of unlimited safe parallelism. Use positive
bounded settings for diagnosis.

**Resume skips or repeats work.** Verify that `--resume-dir` belongs to the
same source paths, output root, task discovery order, schema, and code version.
If any differs, start a new run rather than mixing logs. Preserve the old logs
for diagnosis.

## Workflow-specific failures

**Temporary task outputs collide during a multi-source merge.** Compare source
basenames and task stems before starting. Use distinct output/staging roots or
resolve the collision explicitly. Never merge two semantically different files
under one task identity.

**A partial output exists after interruption.** Stop and inspect logs and the
temporary aggregate. Resume only after identity checks pass. Do not delete a
whole parent directory if it may contain unrelated datasets.

**Ray workers cannot see HDF5 or output paths.** Localize shared storage and
permissions first. Run the same source selection locally, then configure a
cluster with shared paths and compatible Python/dependency versions. Do not
retry a cluster job blindly.

**A regenerated file disappears.** The reference regeneration flow removes a
new file when no replayed episode succeeds. This is a simulator result that
should be diagnosed through task assets, initial states, renderer, and action
compatibility—not bypassed by retaining failed episodes as successful data.

**The images are upside down.** The reference regeneration path applies a
180-degree rotation while collecting observations. Determine whether the HDF5
was already regenerated/corrected before applying any change. Do not rotate
again in core conversion.

**No-op filtering changes episode lengths.** This is expected only for the
approved simulator regeneration boundary. A no-op is near-zero in all action
dimensions except the gripper, with the gripper unchanged from the previous
step (first step checks only the non-gripper dimensions). Do not apply this
filter opportunistically to an already recorded HDF5 conversion.

**A replay ends unsuccessfully.** The reference workflow keeps successful
replays only and records success plus initial state in metainfo. Treat failed
episodes as excluded and investigate simulator version/assets/state setup.
This route does not provide a CPU substitute for simulator execution.

## Stop conditions and escalation

Stop and ask for a decision when the user requests an implicit resize, missing
source keys, an unknown task filename policy, overwrite of an existing target,
Hub push without review, or simulator regeneration without external LIBERO/
robosuite/assets. Escalate shared temp cleanup, Ray scheduling, resume identity,
and Hub behavior to `generic-conversion` when the issue is not LIBERO-specific.
