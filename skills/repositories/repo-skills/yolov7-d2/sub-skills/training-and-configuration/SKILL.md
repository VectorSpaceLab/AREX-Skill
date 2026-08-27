---
name: training-and-configuration
description: "Choose, validate, and launch YOLOv7-d2 Detectron2 configs, custom
  COCO datasets, augmentations, optimizers, and training/evaluation workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Training and Configuration

Use this sub-skill when the user needs to choose a YOLOv7-d2 config, register a custom dataset, inspect model family settings, build a training/evaluation command, tune augmentations, or debug Detectron2 config/data errors.

## Start here

1. Identify the model family from `MODEL.META_ARCHITECTURE` or the user's config name. Read [references/config-and-models.md](references/config-and-models.md).
2. If the user has custom data, validate COCO JSON/image roots before training. Read [references/custom-datasets.md](references/custom-datasets.md) and run [scripts/validate_coco_detection_json.py](scripts/validate_coco_detection_json.py).
3. Build the command with [scripts/build_train_command.py](scripts/build_train_command.py), then review [references/training-workflows.md](references/training-workflows.md).
4. For Python Detectron2 LazyConfig files, read [references/lazyconfig.md](references/lazyconfig.md).
5. For exact API/default facts, read [references/api-reference.md](references/api-reference.md).
6. If anything fails, use [references/troubleshooting.md](references/troubleshooting.md).

## Route by workflow

- Standard YOLO-family detection (`YOLO`, `YOLOV5`, `YOLOV6`, `YOLOV7`, `YOLOV7P`, `YOLOX`, `YOLOF`): use the standard detection trainer pattern.
- SparseInst or mask-only instance segmentation: use the instance-segmentation trainer pattern and mask-aware evaluation notes.
- DETR-family (`Detr`, `AnchorDetr`, `SMCADetr`, `DetrD2go`): use the transformer trainer pattern and DETR optimizer/mapper notes.
- Python LazyConfig files: use the LazyConfig launcher pattern, not the broken LazyConfig demo.
- Anchor recalculation for custom anchor-based data: use [scripts/compute_anchors_from_coco.py](scripts/compute_anchors_from_coco.py) on a valid COCO annotation file.

## Safe checks

Run these before long jobs:

```bash
python scripts/inspect_yolov7_config.py --config path/to/config.yaml
python scripts/validate_coco_detection_json.py --json annotations.json --images image_root
python scripts/build_train_command.py --mode det --config path/to/config.yaml --num-gpus 1 --opts MODEL.WEIGHTS path/to/model.pth
```

These helpers do not train. They help catch missing configs, bad dataset schemas, unresolved `_BASE_` paths, wrong class counts, or unsafe command choices before launching expensive runs.

## Boundaries

- For PyTorch demo inference or COCO evaluation command details, read [../inference-and-evaluation/SKILL.md](../inference-and-evaluation/SKILL.md).
- For ONNX export, ONNXRuntime, TensorRT, quantization, or DETR checkpoint conversion, read [../deployment-and-export/SKILL.md](../deployment-and-export/SKILL.md).
