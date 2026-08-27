---
name: segmentation
description: "Use this YOLOv5 sub-skill for instance-segmentation training,
  validation, prediction, mask data, segmentation checkpoints, and mask
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# YOLOv5 Segmentation

Use this route for YOLOv5 instance segmentation workflows involving `segment/predict.py`, `segment/train.py`, `segment/val.py`, `*-seg.pt` checkpoints, segmentation YAMLs, polygon labels, masks, or mask-specific failures.

## Choose the workflow

- **Predict masks**: read `references/workflows.md` for segmentation prediction command shapes, `--retina-masks`, output directories, and source handling. Use `scripts/plan_segmentation_command.py` before running commands.
- **Train masks**: use the training section for `coco128-seg.yaml`, custom segmentation labels, pretrained vs scratch segmentation configs, DDP, and output planning.
- **Validate masks**: use the validation section for mask metrics, `--overlap`, `--mask-ratio`, confidence/IoU, and exported-format validation handoff.
- **Data formats**: read `references/data-formats.md` before converting detection labels or assuming a dataset is segmentation-ready.

## Common decisions

- Use segmentation checkpoints such as `yolov5s-seg.pt`; do not use plain detection checkpoints for mask workflows unless the task explicitly builds a new segmentation model.
- Use `models/segment/yolov5*-seg.yaml` when training from scratch.
- Treat full COCO segments as large; prefer `coco128-seg.yaml` or a tiny local fixture for smoke work.
- Keep `--project` and `--name` explicit because prediction/training/validation write run artifacts.
- Use CPU for parser/import checks and CUDA for realistic training or high-resolution prediction.

## Handoffs

- Read root `references/datasets-and-weights.md` for segmentation checkpoint names and dataset download risks.
- Route detection-only boxes to `../detection/SKILL.md` and classification to `../classification/SKILL.md`.
- Route export/deployment formats for a segmentation checkpoint to `../export/SKILL.md`.
- Route Flask serving to `../serving/SKILL.md` only if the service itself is the user's task.
