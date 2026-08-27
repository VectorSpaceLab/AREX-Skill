---
name: inference-and-evaluation
description: "Run safe preflight and route legacy Frustum PointNets validation,
  KITTI result writing, and 2D/BEV/3D AP evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference and evaluation

Use this route for checkpoint-backed validation, RGB-detection inference, KITTI
label output, and offline AP evaluation. Read the linked CLI and result
references before launching; the source assumes precomputed frustum data,
2D detector boxes, and a compatible TensorFlow-1 model.

## Route

1. Confirm a checkpoint/model/point/channel match with
   `../training/SKILL.md` and validate the source pickle through
   `../kitti-data-preparation/SKILL.md`.
2. Choose `--from_rgb_detection` only when the input pickle came from detector
   boxes and `--idx_path` is available for frame output.
3. Run `python scripts/validate_kitti_results.py --help` and validate any
   existing result directory before compiling/running the evaluator.
4. Keep inference output and evaluator results in fresh directories. Do not
   overwrite a prior benchmark result.

The evaluator reports 2D, bird's-eye-view, and 3D detection AP. Its native
binary is a platform-specific build artifact and is not bundled here. Full
inference/AP was not executed as verification: CUDA, checkpoints, and KITTI
assets are external gates.

Read [evaluation workflow](references/evaluation-workflow.md),
[KITTI results](references/kitti-results.md), and
[troubleshooting](references/troubleshooting.md). For TensorFlow/CUDA or v2
operator failures route to `../runtime-and-custom-ops/SKILL.md`.
