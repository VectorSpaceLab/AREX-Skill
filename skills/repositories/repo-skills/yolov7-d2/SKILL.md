---
name: yolov7-d2
description: "Operate YOLOv7-d2, a Detectron2-based repository for YOLO-family,
  SparseInst, DETR-family training, inference, evaluation, and ONNX deployment
  workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# YOLOv7-d2 Repo Skill

Use this skill when the task is about the `yolov7_d2` / `yolov7-d2` package or about a Detectron2-style YOLOv7-d2 checkout: choosing configs, training object detectors or instance segmenters, running demos/evaluation, exporting models, converting DETR checkpoints, or debugging this repository's dependency/config/runtime issues.

This skill is self-contained operating guidance distilled from the repository. It does not assume the construction checkout is available. When a task needs runnable project code, use the user's own YOLOv7-d2 checkout or installed package plus the bundled helper scripts and references here.

## First checks

1. Confirm the user's task names YOLOv7-d2, `yolov7_d2`, `yolov7`, Detectron2 configs from this repo, or repo-specific scripts such as `train_det.py`, `demo.py`, `export.py`, or DETR converters.
2. Check installation facts with [scripts/smoke_import_and_config.py](scripts/smoke_import_and_config.py): it imports `yolov7`, injects `add_yolo_config`, and optionally merges a user config.
3. Read [references/installation-and-environment.md](references/installation-and-environment.md) before giving dependency or backend advice.
4. Read [references/model-family-overview.md](references/model-family-overview.md) before choosing between YOLO-family, SparseInst/SOLOv2, DETR-family, YOLOF, or LazyConfig workflows.
5. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/config failures.

## Route by task

- For config selection, custom COCO datasets, training launchers, augmentations, optimizer settings, model-family config maps, or dataset-registration failures, read [sub-skills/training-and-configuration/SKILL.md](sub-skills/training-and-configuration/SKILL.md).
- For PyTorch demo inference, image/video visualization, confidence/NMS flags, W&B inference logging, benchmark planning, or COCO evaluation, read [sub-skills/inference-and-evaluation/SKILL.md](sub-skills/inference-and-evaluation/SKILL.md).
- For ONNX/TorchScript export, ONNXRuntime inference, DETR checkpoint conversion, TensorRT, or quantization, read [sub-skills/deployment-and-export/SKILL.md](sub-skills/deployment-and-export/SKILL.md).

## Minimal install/import guidance

YOLOv7-d2 is built on Detectron2 and PyTorch. The repository metadata is minimal, so users usually need to install a compatible PyTorch/Detectron2 stack first, then install `yolov7_d2` and the runtime packages used by their workflow.

Minimum import/config inspection typically needs:

```bash
python -m pip install torch torchvision
python -m pip install 'detectron2'  # use the Detectron2 install command matching the user's torch/CUDA stack
python -m pip install yolov7-d2 timm nbnb omegaconf pycocotools scipy alfred-py wandb
python - <<'PY'
from detectron2.config import get_cfg
from yolov7.config import add_yolo_config
cfg = get_cfg(); add_yolo_config(cfg)
print(cfg.MODEL.YOLO.CLASSES, cfg.SOLVER.OPTIMIZER, cfg.MODEL.DETR.NUM_OBJECT_QUERIES)
PY
```

Use CUDA only when the user needs real GPU training/inference/export. CPU is enough for config inspection, command planning, and most preflight checks; it is not a substitute for GPU throughput, TensorRT, or long training validation.

## What this skill does not cover

- It does not verify mAP, reproduce benchmark tables, download model weights, or run long training jobs by default.
- It does not promise closed-source or WIP features mentioned in the README unless they are present in the user's code and verified separately.
- It treats TensorRT and quantization paths as optional, toolchain-dependent workflows unless the user provides the needed engine/model/calibration artifacts and hardware.

## Provenance and router metadata

- Source baseline and evidence paths are in [references/repo-provenance.md](references/repo-provenance.md).
- Managed repo-skills router metadata is in [references/repo-routing-metadata.json](references/repo-routing-metadata.json).
