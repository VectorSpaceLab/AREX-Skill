---
name: "libero-conversion"
description: "Guides conversion of LIBERO HDF5 task demonstrations into LeRobot
  datasets and safely evaluates optional simulator-based regeneration, including
  task discovery, state/action schemas, image resolution, execution controls,
  and failure recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LIBERO conversion

Use this route when a user has LIBERO task-suite HDF5 files and wants a local
or Hub-backed LeRobot dataset, or asks whether the files must be regenerated
before conversion. This route covers the LIBERO-specific contract only. For
executor lifecycle, temporary aggregation, and shared adapter behavior, load
[`generic-conversion`](../generic-conversion/SKILL.md).

## Safety boundary

- Treat conversion as a data-writing operation. First inventory source files,
  output roots, temporary roots, and any resume log directory.
- Prefer `--executor local` and `--debug` for a first structural smoke test.
  Do not start Ray, upload to the Hub, or regenerate through a simulator without
  explicit approval and a verified environment.
- The converter reads HDF5 and writes LeRobot data; it does not create missing
  camera modalities or resize images safely on its own. Never silently reshape
  128x128 frames to the declared 256x256 feature shape.
- Simulator regeneration is reference-only in this skill. It requires external
  LIBERO, robosuite, task assets, off-screen rendering, and potentially a large
  HDF5 rewrite; it must not be run as part of planning or validation.

## Route checklist

1. Confirm the source directories, desired output root, LeRobot format/version,
   and whether multiple suites/directories should be merged.
2. Inspect only direct children matching `*.hdf5`; derive the task instruction
   from each filename and reject or separately review files that do not match
   the supported naming convention. See [workflows](references/workflows.md).
3. Validate every selected file's `data` group and each demo's required `obs`
   datasets before scheduling conversion. Check lengths, dtypes, image shapes,
   and finite numeric values using a read-only structural probe.
4. Confirm that RGB frames are 256x256x3, or stop and choose the explicit
   128x128 handling/regeneration path in [data formats](references/data-formats.md).
5. Use the conversion flags and merge rules in [workflows](references/workflows.md).
   Keep local execution as the baseline; use Ray only after its dependencies
   and cluster ownership are confirmed.
6. After conversion, inspect feature metadata, episode/task counts, image
   dimensions, action range, and state widths before any Hub push.
7. When a failure occurs, use [troubleshooting](references/troubleshooting.md)
   and preserve the source and logs. Do not retry by deleting an unrelated
   output or by changing schemas to make validation pass.

## LIBERO-specific data transformation

Each demo is emitted frame-by-frame with its task instruction attached. The
six-dimensional end-effector pose is concatenated with the two-dimensional
LIBERO gripper state to form the eight-dimensional `observation.state`. The
seven-dimensional action keeps the first six values and transforms the final
command with `1 - clip(value, 0, 1)`, preserving the repository's gripper
inversion convention. This is a semantic conversion, not a generic numeric
normalization; record it in provenance.

Do not route RLDS/TFDS input, RoboCasa files, or LeRobot version migrations
through this sub-skill. Choose the corresponding sibling route at the root.
Do not treat a successful file open as proof that the task is convertible:
shape, frame alignment, and feature-version checks are required before the
writer is started.

For a synthetic smoke case, use a two-frame `data/demo_0` fixture with all
required arrays and verify only key presence, widths, image dimensions, and
the final action component. This gives coverage of the difficult schema path
without invoking a converter, codec, Ray, Hub, or simulator.

The standard feature contract is two RGB video streams (`agentview_rgb` and
`eye_in_hand_rgb`) at 256x256x3, an 8-wide combined state, separate 6-wide
end-effector, 7-wide joint, and 2-wide gripper state streams, and a 7-wide
action. The canonical defaults are 20 FPS and Franka. Do not infer a different
robot or FPS merely from a directory name.

## Handoff

Report selected files, skipped filename mismatches, source shape/dtype checks,
transformation choices, executor and safety flags, output metadata checks, and
whether regeneration was not run. Preserve unresolved optional-dependency or
schema gaps explicitly.

Evidence for this route was distilled from the repository's LIBERO README,
`libero_h5.py`, and `regenerate_libero_dataset.py`; those artifacts are
provenance only and are not runtime dependencies.
