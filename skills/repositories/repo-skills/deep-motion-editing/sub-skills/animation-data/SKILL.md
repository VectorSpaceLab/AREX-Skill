---
name: animation-data
description: "Inspect and validate deep-motion-editing animation data: BVH
  skeletons and motion frames, quaternion/root-position tensors, OpenPose JSON
  directories, kinematics inputs, and foot-contact cleanup outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Animation data

Use this skill when a task crosses the data boundary of deep-motion-editing:
inspect a BVH before loading it, check a skeleton/frame-time/topology mismatch,
understand quaternion/root-position arrays, validate an OpenPose directory, or
explain `raw.bvh` versus `fixed.bvh`. This is a format and safety layer, not a
model runner.

## Route the task

- For a retargeting model, character pairing, simplified joint lists, or
  `BVH_file`/`BVH_writer` integration, use
  [motion-retargeting](../motion-retargeting/SKILL.md) after validating the
  inputs here.
- For 3D/2D style-transfer inference, normalization `.npz` files, or generated
  motion orchestration, use
  [motion-style-transfer](../motion-style-transfer/SKILL.md). Preflight its
  BVH or OpenPose input here.
- For Blender import, axis swapping, rendering, or skinning, use
  [blender-visualization](../blender-visualization/SKILL.md); BVH is Y-up in
  the repository while Blender handling is a separate runtime.

## Safe first pass

1. Keep source and destination paths explicit. This is a script-oriented
   repository with legacy working-directory/`sys.path` assumptions, not an
   installed package.
2. Inspect without project imports first:
   ```bash
   python <animation-data-skill>/scripts/inspect_bvh.py INPUT.bvh
   python <animation-data-skill>/scripts/inspect_bvh.py INPUT.bvh --json
   python <animation-data-skill>/scripts/inspect_bvh.py INPUT.bvh --round-trip OUT.bvh
   python <animation-data-skill>/scripts/validate_openpose_json.py JSON_DIR
   ```
   Replace `<animation-data-skill>` with the installed skill directory. These
   helpers are read-only except for an explicitly named `--round-trip` output;
   they do not download, train, edit the input, or invoke Blender.
3. Stop on malformed hierarchy, non-finite motion, frame-count/channel
   mismatch, duplicate names, or unexpected topology. A successful text
   preflight does not prove that the legacy NumPy/PyTorch runtime executes.
4. For a copied tiny fixture, compare the summary before and after a
   round-trip. Joint order, parent indices, offsets, frame count, frame time,
   and finite motion should remain equivalent. Formatting and explicit zero
   length leaf `End Site` records may differ.

## Central BVH contract

- A BVH has `HIERARCHY` (root/joint names, parent tree, static offsets,
  channels, optional `End Site`) and `MOTION` (`Frames`, `Frame Time`, one
  channel row per frame).
- The normal convention is root XYZ position followed by local Euler rotations;
  non-root joints have three rotation channels. `Frame Time` is seconds per
  frame, not FPS. FPS is `1 / frame_time`.
- The shared representation is frame-major: local rotations `(T, J, 4)` in
  scalar-first `(w, x, y, z)` quaternion form, root translation `(T, 3)`,
  offsets `(J, 3)`, and `parents (J,)` with root `-1`. Euler channels are
  converted to quaternions by the source loaders when requested.
- Kinematics composes local rotation with the parent world transform, applies
  the child offset, and adds the parent position. Parent indices must precede
  children for legacy global-transform helpers.
- Retargeting `BVH_file` recognizes hard-coded simplified skeleton families,
  retains a selected joint order and five end effectors, and writes a
  simplified 30-FPS BVH through `BVH_writer`. Do not force a new topology into
  the nearest family; route new mappings to motion-retargeting.
- Style-transfer `AnimationData` stores `[J*4 quaternion values, root xyz,
  root-facing pivot, 4 contact flags]` as `(T, channels)` and exposes network
  features as `(channels, T)`. The standard CMU skeleton has 31 full joints and
  selects 21 model joints; its YAML is authoritative for indices.

Read [data-formats](references/data-formats.md) for schemas and shape tables,
[api-reference](references/api-reference.md) for callable contracts, and
[troubleshooting](references/troubleshooting.md) before repairing data.

## OpenPose JSON directory

Pass a directory of JSON frames produced by OpenPose, not a video or JSON
array. The source loader lexically sorts entries, truncates to a multiple of
four, selects `people[0]`, and expects `pose_keypoints_2d`,
`hand_left_keypoints_2d`, and `hand_right_keypoints_2d`. Each keypoint is
`(x, y, confidence)`; confidence is discarded. The converted sequence has 21
style joints. Missing detections may be carried forward/backward by the legacy
loader, but that is an explicit repair policy, not valid tracking evidence.
Use stable zero-padded names such as `000000_keypoints.json`; the validator
reports gaps, duplicates, missing keys, empty detections, and the effective
multiple-of-four prefix without changing files.

## Foot contact and output semantics

Style-transfer contacts are four binary channels in left-foot pair then
right-foot pair order (`[4, T]` after transpose); the CMU YAML identifies
actual feet. They are low-velocity constraints, not BVH channels. Retargeting
uses a separate end-effector ordering, so contact arrays are not interchangeable
without an explicit mapping.

`raw.bvh` is direct network output reconstructed to BVH. `fixed.bvh` is a
separate derivative after contact intervals are held at average global
positions, short gaps interpolated, and inverse kinematics used to adjust
rotations/root translation. Preserve both. Cleanup can move the root and feet
and is not a physical-correctness guarantee. Route orchestration and model
execution to motion-style-transfer or motion-retargeting; this skill only
preflights and explains the boundary. The legacy `remove_fs.py` launcher is not
bundled because it assumes paths and performs file writes.

## Compatibility and limits

`utils/Animation.py` imports removed `numpy.core.umath_tests` and can fail on
modern NumPy with `ModuleNotFoundError: No module named 'numpy.core.umath_tests'`
(or an equivalent `_umath_tests` load error). Text BVH inspection and these
standalone helpers remain usable. Prefer them, or the newer `BVH.py`/
`BVH_mod.py` path when its dependencies are available; do not claim the old
`Animation` transform methods ran.

A bounded recovery decision is: (1) structural inspection only; (2) in a
throwaway environment, test a compatible older NumPy pin if the exact legacy
path is required; or (3) apply a reviewed local patch replacing only the
removed matrix multiply call with equivalent `numpy.matmul`, then run the
copied tiny fixture round-trip and FK checks. Never pin or patch globally, and
do not infer quaternion averaging, Maya utilities, IK, or Blender support from
an import success. NumPy/SciPy/PyYAML/PyTorch, OpenPose, and Blender are
optional workflow dependencies; external data and full model runs remain
user-controlled and potentially expensive.

Bundled helpers: [inspect_bvh.py](scripts/inspect_bvh.py) and
[validate_openpose_json.py](scripts/validate_openpose_json.py). Both expose
`--help`, avoid network/training/destructive behavior by default, and do not
make the original source checkout a runtime dependency.