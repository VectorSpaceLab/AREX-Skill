---
name: int8-benchmarking
description: "Routes INT8 calibration, calibration-image preparation, and
  benchmark tuning tasks for DeepStream-Yolo models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# INT8 benchmarking

Use this sub-skill when the task is about calibration-enabled builds, `calib.table`, INT8 engine generation, or interpreting the benchmark notes and NMS values.

## Trigger phrases

- INT8 calibration
- `calib.table`
- `INT8_CALIB_IMG_PATH`
- `INT8_CALIB_BATCH_SIZE`
- `OPENCV=1`
- benchmark table
- NMS threshold tuning
- performance comparison

## Include here

- The OpenCV-backed calibration build path.
- Calibration image list preparation.
- `int8-calib-file` and related DeepStream config edits.
- Benchmark notes, NMS values, and performance caveats.
- Troubleshooting for calibration-specific failures.

## Exclude or route elsewhere

- Exporting the checkpoint to ONNX: use `model-conversion`.
- Single-model deployment without calibration: use `deployment`.
- Multiple GIE layout work: use `multi-gie`.
- Skill maintenance or import/export logic.

## How to use this route

1. Read `references/workflows.md` for the calibration flow.
2. Read `references/benchmark-notes.md` for the benchmark table and NMS defaults.
3. Use `scripts/make-calibration-list.sh` to build `calibration.txt` from a directory of images.
4. Use `scripts/build-nvdsinfer-plugin.sh --output-dir ./deepstream-yolo-runtime` to rebuild the library with `OPENCV=1` when calibration support is required.
5. Use `deployment` only after the calibration build path is ready.
6. Read `references/troubleshooting.md` if the calibration build or runtime fails.

## What a future agent should be able to do here

- Decide whether the calibration build path needs `OPENCV=1`.
- Build a valid calibration image list from a COCO-style or custom image directory.
- Edit the infer config so INT8 calibration writes `calib.table` and uses the INT8 engine path.
- Read the benchmark table without treating it as a universal default.

## Common failure signals

- `libopencv-dev` missing
- `OPENCV=1` build path not enabled
- `INT8_CALIB_IMG_PATH` points to a stale list
- `calib.table` is not written
- NMS or threshold values are not matched to the family

## Linked helpers

- `scripts/make-calibration-list.sh` — build `calibration.txt` from a directory of images.
- `scripts/build-nvdsinfer-plugin.sh` — build the custom library in a fresh runtime tree with `OPENCV=1` when needed.
- `references/workflows.md` — calibration and run steps.
- `references/benchmark-notes.md` — benchmark and NMS guidance.
- `references/troubleshooting.md` — calibration-specific failure modes.
