---
name: classification
description: "Use this YOLOv5 sub-skill for image-classification training,
  validation, prediction, ImageFolder data, YOLOv5-cls checkpoints, and
  torchvision model choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# YOLOv5 Classification

Use this route for YOLOv5 image classification workflows involving `classify/predict.py`, `classify/train.py`, `classify/val.py`, `yolov5*-cls.pt` checkpoints, torchvision classifier model names, ImageFolder datasets, or classification-specific output/troubleshooting.

## Choose the workflow

- **Predict classes**: read `references/workflows.md` for source handling, image size, device, save options, and classifier output expectations.
- **Train classifiers**: use the training section for named datasets, local ImageFolder directories, pretrained models, freeze/dropout/cutoff choices, and DDP.
- **Validate classifiers**: use the validation section for accuracy checks, ImageNet-style layout, batch size, half/DNN, and output directories.
- **Data layout**: read `references/data-formats.md` before using a custom directory or named dataset.

Use `scripts/plan_classification_command.py` to preview commands without downloads, training, media processing, or output writes.

## Common decisions

- Use `yolov5s-cls.pt` or a small torchvision model for smoke-scale planning.
- Use local ImageFolder paths for reproducible work; named datasets may download.
- Classification uses probabilities/top-k outputs, not boxes or masks.
- Keep `--project`, `--name`, and `--exist-ok` explicit.
- Use CPU for parser/import checks and CUDA for realistic training.

## Handoffs

- Route detection boxes to `../detection/SKILL.md` and masks to `../segmentation/SKILL.md`.
- Route checkpoint export to `../export/SKILL.md` after selecting a classifier checkpoint.
- Read root `references/datasets-and-weights.md` for checkpoint names and ImageNet download risks.
