# RoboCasa troubleshooting

Use the symptom, likely cause, and stop condition together. These remedies are
planning guidance; they do not bundle the RoboCasa source checkout or execute
simulation/data conversion.

## Installation and import

### `ModuleNotFoundError: h5py`, `numpy`, or LeRobot

**Cause:** The conversion environment is incomplete or the wrong interpreter
is active. Install the required packages in the selected isolated environment,
then re-run safe import and signature probes. Pin a mutually compatible
LeRobot/HDF5 stack rather than copying imports from a different release.

**Stop when:** the selected `LeRobotDataset` import or its create/frame/save
contract cannot be verified. Do not fall back to a guessed `lerobot.datasets`
import and do not write a partial output.

### `robocasa` or `robosuite` cannot import

**Cause:** The request crossed from HDF5 conversion into subset/rerender or
playback, but simulator packages are absent, incompatible, or not on the
active interpreter's path.

**Recovery:** Separate the conversion-only plan from the simulator plan. For
rerendering, install the RoboCasa and robosuite versions expected by the
recorded `env_args`, required MuJoCo/offscreen renderer support, and assets;
then run an explicit environment and camera preflight. No amount of LeRobot
installation supplies RoboCasa assets.

### Renderer starts but cannot find assets or camera

**Cause:** RoboCasa asset registry, model XML, task environment, camera name,
or renderer backend does not match the recording.

**Recovery:** Parse `data.attrs['env_args']`, inspect one demo's `model_file`,
and compare camera names and task configuration. Repair the simulator setup or
obtain a matching source. Do not rewrite camera names or omit a camera to make
rerendering proceed.

## Data and configuration validation

### `KeyError` for `data`, `obs`, camera, state, action, `mask`, or `env_args`

**Cause:** The file is not the expected RoboCasa release/layout, the optional
subset mask was requested but is absent, or a rerender-only key was assumed to
exist in an original recording.

**Recovery:** Inspect groups, attributes, and one demo read-only. Route based on
the missing key: conversion needs the required RGB/state/action/language keys;
subset selection needs a named mask; rerender needs `env_args`, model XML, and
initial state. Do not select all demos as an implicit substitute for a missing
mask.

### `JSONDecodeError` or missing `ep_meta['lang']`

**Cause:** HDF5 attributes can be bytes, malformed JSON, or a different
metadata schema.

**Recovery:** Decode bytes, parse once, require an object and a `lang` field,
and preserve the raw attribute for diagnosis. Obtain an explicit task mapping
if language is not available. Never use a filename or a guessed English label.

### Image shape or channel mismatch

**Cause:** Original RoboCasa data is often 128x128, arrays may be CHW/BGR, or
one camera has a different length/resolution. The default feature contract is
HWC RGB `(256,256,3)`.

**Recovery:** Inspect shape, dtype, value range, and a documented color/axis
convention for every camera. For a 256x256 requirement, use matching
simulator rerendering or a trusted preprocessing step with an explicitly
changed contract. Do not silently resize, transpose, or label BGR as RGB.

### State/action length mismatch

**Cause:** A demo has truncated observations, a different control frequency,
or action/state arrays from different timelines.

**Recovery:** Compare the first dimension of all three images, position,
quaternion, gripper, and action arrays. Isolate the demo and preserve a reason;
only pad/truncate under an explicit, task-approved policy. Do not let the
converter's loop length hide dropped or unaligned frames.

### Unexpected state dimension

**Cause:** The concatenated source components are not 3+4+2, or quaternion and
gripper keys represent a different embodiment.

**Recovery:** Reconfirm the source schema and robot type. Do not reshape into
nine values or call simulator state a policy state. Use a new feature contract
only if the downstream consumer accepts it.

## CLI/API misuse and output safety

### `unrecognized arguments`

**Cause:** The source CLI exposes only `--raw-dir`, `--local-dir`, and
`--repo-id`. Subset, rerender, depth, segmentation, Hub push, resume, and
filter flags are not part of that converter.

**Recovery:** Perform subset/rerender as a separate pre-stage and pass the
resulting HDF5 directory to conversion. Do not alter a script's CLI in place
without updating the contract and validation.

### Existing output disappeared

**Cause:** The observed converter calls recursive deletion on `local_dir`
before dataset creation. The rerender flow can also delete its output when no
episode succeeds.

**Recovery:** Restore from the reviewed backup, inspect logs, and select a new
output path. Before a retry, verify the path is not an input directory and
require explicit replacement approval. Treat any existing output deletion as a
known destructive side effect, never as routine cleanup.

### Conversion stops after some episodes

**Cause:** A malformed demo raises during HDF5 read, JSON parsing, frame
addition, video encoding, or LeRobot finalization. The default flow does not
provide a safe resume/skip protocol.

**Recovery:** Keep the original source, isolate the failing demo, inspect
lengths/shapes/metadata, and write a fresh output. Record which episodes were
saved; do not append blindly to a partially finalized dataset. If robust skip
or resume semantics are required, design and verify them as a new wrapper.

### `repo_id` or Hub credential confusion

**Cause:** The dataset writer may use a repository identifier for metadata even
when the command writes only to a local root. A repo ID is not permission to
push.

**Recovery:** Keep local conversion and Hub publication as separate approved
operations. Validate local output first; publish only with explicit credentials,
network permission, and a reviewed dataset identity.

## Subset-specific failures

### Mask IDs produce zero demos

**Cause:** IDs are bytes versus strings, names include a prefix difference, or
the selected mask belongs to another file/task.

**Recovery:** Decode and normalize only the representation (not the ID's
meaning), compare against exact `data` keys, report every missing ID, and
confirm the file/task pairing. Never silently fall back to all demos.

### Subset file loses rerender ability

**Cause:** The copy preserved demo groups but omitted `data` attributes such as
`env_args`.

**Recovery:** Recreate the subset from the original, copying all `data`
attributes and each selected demo group. Verify `env_args`, `model_file`, and
initial states before simulator use.

## Rerender, camera, and success filtering

### `reset_to` cannot restore a demo

**Cause:** Missing `model_file`, malformed initial `states[0]`, stale `env_args`,
or an incompatible RoboCasa/robosuite playback API.

**Recovery:** Test one representative demo with the exact environment and
assets. Reject or separately diagnose demos whose saved model/state cannot be
restored. Do not substitute a fresh environment reset; that changes the
trajectory and invalidates the rerender.

### Depth is empty, inverted, or has unexpected units

**Cause:** Offscreen depth was not enabled, near/far values were not converted,
or the renderer's normalized depth convention differs from the expected one.

**Recovery:** Require `camera_depths=True`, inspect near/far clipping values,
validate one pixel/range against a known geometry case, and document whether
`depth` is normalized or `depthW` is world-depth. Do not call an RGB resize a
depth recovery.

### Segmentation is missing or labels are wrong

**Cause:** Camera segmentation was not enabled, the chosen mode (`element`,
`instance`, or `semantic`) is unsupported by the installed environment, or
label IDs changed with assets.

**Recovery:** Enable and verify an explicit segmentation mode in the external
simulator; inspect dtype, shape, and label semantics on one frame. Keep the
original mode in metadata. Do not infer segmentation from RGB or reuse labels
from another asset release.

### Camera intrinsics/extrinsics disagree

**Cause:** Different image dimensions/FOV, world versus model-relative pose,
MuJoCo camera-axis correction, image row flips, or a different robosuite API.

**Recovery:** Recompute matrices from the actual simulator and record camera
name, size, FOV, coordinate convention, and units. Intrinsics use the 3x3
pinhole matrix; extrinsics are 4x4 poses with a camera-axis correction. Do not
compare `extrinsicsR` to world extrinsics without accounting for their frame.

### All rerendered episodes are dropped

**Cause:** Action replay never reaches terminal success, the action format is
wrong for the environment, physics/API versions differ, or the success check
is stricter than the original annotation.

**Recovery:** Run only a single approved debug demo in an isolated simulator
output path, inspect reset state and first action, and compare the environment
success predicate. Treat zero saved demos as an unsuccessful rerender, not as
proof that the source dataset is empty. The reference flow deletes an empty
output, so preserve logs and the original input first.

### Rerender output has fewer episodes than input

**Cause:** The workflow saves only episodes whose terminal/success check is
true; unsuccessful or wrong-action trajectories are intentionally omitted.

**Recovery:** Record input/output IDs and per-demo failure reasons. If the user
requires all episodes, do not use this success-filtered output as a drop-in
replacement; use the original or a separately specified retention policy.

## Explicitly unsupported shortcuts

- Do not create depth, segmentation, or calibration by interpolation from RGB.
- Do not claim a 128x128 file satisfies the fixed 256x256 contract.
- Do not copy the simulator or notebook into a runtime skill.
- Do not start rendering, download assets, run a full conversion, push to Hub,
  or overwrite a directory during a static check.
