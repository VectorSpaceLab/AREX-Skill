---
name: part-segmentation-workflows
description: "ShapeNetPart part-segmentation training, evaluation, inference,
  data layout, and one-hot command workflow guidance for the pointnet2
  repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Part Segmentation Workflows

Use this sub-skill when the user asks about ShapeNetPart object part segmentation in this PointNet++ repository: training on the official ShapeNetPart normal dataset, evaluating a checkpoint, choosing the one-hot category-conditioned variant, or adapting the legacy single-category visualization path.

## Route first by workflow

- **All-category plain segmentation**: use `part_seg/train.py` with model `pointnet2_part_seg`; evaluate an existing checkpoint with `part_seg/evaluate.py`. Start with [references/workflows.md](references/workflows.md#all-category-plain-training-and-evaluation).
- **All-category one-hot segmentation**: use `part_seg/train_one_hot.py` with model `pointnet2_part_seg_msg_one_hot`; the dataset must return a per-shape category label in addition to per-point part labels. Start with [references/workflows.md](references/workflows.md#one-hot-category-conditioned-training).
- **Single-category visualization / test-time inference**: treat `part_seg/test.py` as a legacy reference, not a reliable drop-in script, because it has a `ROOT_DIR` bug and stale dataset/model assumptions. Start with [references/workflows.md](references/workflows.md#single-category-test-time-visualization).
- **Dataset diagnosis before training**: run the bundled validator in [scripts/validate_shapenetpart_layout.py](scripts/validate_shapenetpart_layout.py) and read [references/data-formats.md](references/data-formats.md).
- **Command construction**: prefer [scripts/build_part_seg_command.py](scripts/build_part_seg_command.py) over copying the original background shell snippets.

## Mandatory checks before suggesting a run

1. Confirm the user has the ShapeNetPart root with `synsetoffset2category.txt`, `train_test_split/*.json`, and category folders matching the intended loader. See [references/data-formats.md](references/data-formats.md#normal-all-category-layout-used-by-training-and-evaluation).
2. Confirm whether the user wants **plain** or **one-hot** training. Do not pass the one-hot model to `evaluate.py`; the source evaluator only builds the plain model interface.
3. Confirm the runtime can import TensorFlow 1.x and the PointNet++ custom ops needed by `pointnet_sa_module`, `pointnet_sa_module_msg`, and `pointnet_fp_module`. CPU-only validation is enough for data/command checks, but native model execution is a legacy CUDA/custom-op path.
4. For visualization requests, explain that `test.py` needs patching before use; do not present it as a verified runnable script. See [references/troubleshooting.md](references/troubleshooting.md#root_dir-and-stale-testpy-visualization-path).

## Bundled helpers

- [scripts/build_part_seg_command.py](scripts/build_part_seg_command.py) builds shell commands for plain training, one-hot training, plain evaluation, and legacy test visualization with safer defaults and workflow guards.
- [scripts/validate_shapenetpart_layout.py](scripts/validate_shapenetpart_layout.py) validates ShapeNetPart normal and legacy `points/points_label` layouts, split JSON membership, empty selected splits, and basic label/column schema.
- [scripts/smoke_shapenetpart_loader.py](scripts/smoke_shapenetpart_loader.py) creates a tiny temporary ShapeNetPart-style fixture and runs the validator; use it to check the bundled validator itself without requiring the real dataset.

## Evidence and limits

This sub-skill distills repository evidence from the README, `part_seg/command*.sh`, `part_seg/train*.py`, `part_seg/evaluate.py`, `part_seg/test.py`, `part_seg/part_dataset*.py`, and the two `pointnet2_part_seg*` model definitions. It intentionally does not copy the raw trainers because they are Python-2-era, checkpoint/data/GPU heavy, and contain repo-relative assumptions. Workflow-specific failure modes are in [references/troubleshooting.md](references/troubleshooting.md); data contracts are in [references/data-formats.md](references/data-formats.md).
