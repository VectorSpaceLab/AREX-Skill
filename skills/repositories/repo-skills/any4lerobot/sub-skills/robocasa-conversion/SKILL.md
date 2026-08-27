---
name: "robocasa-conversion"
description: "Guides conversion of RoboCasa HDF5 demonstrations to LeRobot and
  plans safe subset extraction or simulator rerendering when RGB, depth,
  segmentation, or calibration data are missing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RoboCasa conversion

Use this route for RoboCasa kitchen demonstrations stored as HDF5 when the
requested result is a LeRobot dataset, a deliberately selected demo subset, or
a rerendered HDF5 source with 256x256 camera observations. It owns RoboCasa,
robosuite, camera, and rerender prerequisites. It does **not** own LIBERO,
generic adapter design, or LeRobot version migration.

## Choose the boundary first

1. **Conversion only**: use an already suitable HDF5 tree. The converter
   expects three RGB camera streams, a 9-value state, a 12-value action, and
   per-episode language. It does not resize, rerender, validate, or export
   depth/segmentation/calibration features for you.
2. **Subset first**: select demo IDs from the HDF5 `mask` group before
   conversion. Preserve the `data` group attributes, especially `env_args`,
   because later environment reset/rerendering depends on them.
3. **Rerender first**: use a separately prepared RoboCasa/robosuite simulator
   environment when the source is 128x128 or lacks depth, segmentation, or
   camera matrices. Rerendering is an external, simulator-backed workflow;
   follow the ownership and safety boundary in [workflows](references/workflows.md).

Do not silently choose rerendering. Ask whether the user wants only the RGB
LeRobot result, a smaller subset, or a new HDF5 with additional modalities.

## Hard preflight gates

- Keep RoboCasa, robosuite, MuJoCo/offscreen-rendering dependencies, and the
  RoboCasa assets in a separately managed environment. HDF5 conversion alone
  needs Python HDF5/NumPy support and a compatible LeRobot dataset writer;
  simulator rerendering additionally needs the actual RoboCasa environment,
  robosuite playback/reset support, assets, and a functioning offscreen
  renderer. Missing optional simulator packages are a stop condition, not a
  reason to fabricate depth or segmentation.
- Treat the source-derived LeRobot API as a compatibility gate: verify that
  `lerobot.datasets.lerobot_dataset.LeRobotDataset` is importable and that its
  `create(..., repo_id, robot_type, root, fps, features)` and
  `add_frame`/`save_episode`/`finalize` contract exists in the selected
  environment. Do not guess a replacement import path or mix LeRobot versions.
- Inspect the HDF5 structure and dtypes before allowing any output deletion.
  Confirm all expected demos have equal frame counts across images, state
  components, and actions, and that every image is already RGB `256x256x3`.
- Select a new, dedicated output directory. The source-derived converter
  recursively finds HDF5 files and deletes an existing `local_dir` before it
  creates the LeRobot dataset. Never point it at a raw-data, source, or shared
  directory. Back up or rename any existing output and obtain explicit approval
  before destructive replacement.
- This route has no implicit Hub push. A `repo_id` is still part of the
  LeRobot metadata contract; keep publishing, credentials, and network
  operations outside the conversion preflight unless separately approved.

## Conversion contract

Use the complete CLI contract and output behavior in
[workflows](references/workflows.md), and the HDF5/feature tables in
[data formats](references/data-formats.md). The distilled source behavior is:

- Input discovery is recursive over `*.hdf5` below `--raw-dir`.
- Output metadata uses robot type `PandaOmron`, 20 FPS, three RGB video
  features (`robot0_agentview_right`, `robot0_agentview_left`, and
  `robot0_eye_in_hand`), a 9-dimensional float32 state, and a 12-dimensional
  float32 action.
- For each demo, concatenate base-to-end-effector position (3), quaternion
  (4), and gripper position (2) into the 9-value state. Read `ep_meta` as JSON
  and use its `lang` value as the task text on every frame.
- Add frames in source order and close each demo with `save_episode`; finalize
  only after all input files are processed. A malformed demo can therefore
  fail the run rather than being safely repaired. Preflight and isolate input
  files when partial conversion is unacceptable.
- Extra rerendered HDF5 observations are not automatically represented in the
  five-feature LeRobot schema. If depth, segmentation, or calibration must be
  retained, define additional LeRobot features and validate their shapes before
  writing; do not claim that the default converter preserved them.

## Subset and rerender routing

Subset selection is a data-copy operation, not a conversion filter. Read a
named mask such as `30_demos` or `100_demos`, decode its demo IDs, copy matching
`data/<demo_id>` groups, and copy every attribute on `data`. Check for missing
IDs and report them instead of silently producing an incomplete subset.

Rerender only when the user accepts simulator prerequisites, significant I/O,
and success-based episode dropping. It resets each demo from its saved model
XML and initial simulator state, warms the environment with ten dummy actions,
replays the recorded actions, collects RGB/depth/segmentation/calibration and
state data, and saves only episodes that finish successfully. A rerender can
therefore reduce episode count and is not a lossless copy. The output HDF5 is
opened in write mode and is deleted when no episode succeeds; use a new output
path and preserve the original.

For camera matrix conventions and the depth/segmentation decision tree, use
[data formats](references/data-formats.md). For failure recovery, missing
assets, stale metadata, shape errors, unsafe deletion, and success filtering,
use [troubleshooting](references/troubleshooting.md).

## Difficult synthetic case

For verification, create a tiny **synthetic structural fixture** representing an
original 128x128 HDF5 with RGB only, no depth/segmentation keys, a valid
`env_args`, and an existing output directory containing an unrelated sentinel
file. The expected decision is to refuse a claimed 256x256 RGB+depth/segmentation
conversion, route to external RoboCasa/robosuite rerendering, and warn that the
observed conversion would recursively delete the output before writing. A second
variant can include a mask with one missing demo ID and assert that the subset
plan reports the missing ID while preserving `data` attributes. Do not invoke
the converter, simulator, notebook, or any large write for these cases.

## Verification and handoff

Before conversion, run only safe structural checks: list HDF5 keys, inspect
attributes, compare per-key lengths, verify image shape/channel order, parse
`ep_meta`, and check state/action dimensions. A tiny synthetic HDF5 fixture may
exercise this validator, but must not invoke LeRobot writing or simulation.

After a conversion, inspect the generated metadata and one episode without
relying on a Hub or simulator. Confirm FPS, robot type, task text, frame count,
three video feature shapes, state/action shapes, and that the output path was
not an input path. Mark rerender and full conversion trials as unverified when
external data, assets, rendering, or large writes were unavailable.

Evidence for this route was distilled from the RoboCasa workflow README, its
HDF5 converter, the reference-only regeneration and camera helpers, and the
subset notebook's mask/copy intent at the inspected repository snapshot. Those
artifacts are provenance only; this skill has no runtime dependency on a source
checkout, notebook, absolute path, or bundled simulator script.
