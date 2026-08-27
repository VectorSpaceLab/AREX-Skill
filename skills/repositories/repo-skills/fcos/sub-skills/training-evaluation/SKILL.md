---
name: training-evaluation
description: "Builds and troubleshoots FCOS training, evaluation, distributed
  launch, checkpoint, and benchmark-style command workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# FCOS Training and Evaluation

Use this sub-skill when the user asks for FCOS training, COCO/VOC/Cityscapes evaluation, distributed launch, checkpoint handling, AP reproduction, `MODEL.WEIGHT`, `OUTPUT_DIR`, `TEST.IMS_PER_BATCH`, or OOM/runtime failures during train/test workflows.

## Start here

1. Read [`references/cli-reference.md`](references/cli-reference.md) for flags and override semantics.
2. Read [`references/workflows.md`](references/workflows.md) for single-GPU, multi-GPU, evaluation, and OOM-safe command recipes.
3. Use [`scripts/build_train_command.py`](scripts/build_train_command.py) and [`scripts/build_eval_command.py`](scripts/build_eval_command.py) to produce commands without starting long jobs.
4. Use [`scripts/remove_solver_states.py`](scripts/remove_solver_states.py) to create a checkpoint copy without optimizer/scheduler/iteration state.
5. Read [`references/checkpoints.md`](references/checkpoints.md) when changing `MODEL.WEIGHT`, resuming, or publishing weights.
6. Read [`references/troubleshooting.md`](references/troubleshooting.md) for dataset, CUDA/NCCL, OOM, SyncBN, and benchmark limitations.

## Boundaries

- Route YAML selection, dataset layout validation, and custom dataset planning to [`../data-configs/SKILL.md`](../data-configs/SKILL.md).
- Route one-image detector API or display demos to [`../inference-demo/SKILL.md`](../inference-demo/SKILL.md).
- Route ONNX export to [`../onnx-export/SKILL.md`](../onnx-export/SKILL.md).
- Route source-code changes or test triage to [`../internals-maintenance/SKILL.md`](../internals-maintenance/SKILL.md).

## Backend/cost rule

Training and full evaluation are not safe smoke tests. They require datasets, weights, compiled extensions, and usually GPUs. Use command builders and config validation first; run full jobs only after the user approves data, weight downloads, GPU use, output locations, and expected runtime.
