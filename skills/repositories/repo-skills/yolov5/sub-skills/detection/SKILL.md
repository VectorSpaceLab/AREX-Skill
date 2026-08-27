---
name: detection
description: "Use this YOLOv5 sub-skill for object-detection training,
  validation, inference, PyTorch Hub loading, detection datasets, and checkpoint
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# YOLOv5 Detection

Use this route for bounding-box detection requests involving the YOLOv5 clone-run entrypoints, PyTorch Hub model loading, detection YAMLs, pretrained detection checkpoints, or detection-specific errors.

## Choose the workflow

- **Predict/infer**: read `references/workflows.md` for image, directory, video, glob, webcam, screenshot, URL, and stream source planning. Use `scripts/plan_detection_command.py` before running a command with downloads, media, or output writes.
- **Train/fine-tune**: use the training section for `train.py`, custom data YAMLs, pretrained vs scratch training, image/batch/device choices, resume, DDP, and output directories.
- **Validate/evaluate**: use the validation section for `val.py`, data/weights pairing, confidence/IoU, task modes, JSON/plot output, and exported-format validation handoff.
- **PyTorch Hub/local API**: read `references/api-reference.md` for `hubconf.custom`, standard `yolov5n/s/m/l/x` functions, `autoshape`, device selection, and cache behavior.

## Common decisions

- Start with `yolov5n` or `yolov5s` and a tiny local fixture when the goal is a smoke check.
- Use explicit local checkpoint and data paths for offline or reproducible work; names such as `yolov5s.pt` may download.
- Match the detection checkpoint and detection YAML to the class count. Do not use `*-seg.pt` or `*-cls.pt` here.
- Set an explicit `--project` and `--name` when output placement matters. `--exist-ok` is an overwrite policy, not a harmless default.
- Use `--device cpu` for deterministic parser/import checks. Use CUDA for realistic training or half precision.
- Treat webcam, RTSP/HTTP, YouTube, screen capture, and remote URLs as network/device workflows, not safe defaults.

## Handoffs

- Read root `references/datasets-and-weights.md` before downloads or custom data.
- Route segmentation to `../segmentation/SKILL.md` and classification to `../classification/SKILL.md`.
- Route model conversion or backend runtime selection to `../export/SKILL.md` after a checkpoint is selected.
- Route HTTP serving to `../serving/SKILL.md`; this route owns model behavior, not the Flask service contract.
