---
name: yolov5
description: "Use this skill for clone-run Ultralytics YOLOv5 workflows:
  detection, segmentation, classification, export, benchmarks, datasets,
  weights, and Flask REST serving."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# YOLOv5 Repo Skill

Use this skill when a user asks about Ultralytics YOLOv5 repository workflows: object detection, instance segmentation, image classification, PyTorch Hub loading, dataset YAMLs, pretrained weights, model export, benchmarks, or the bundled Flask REST API example.

YOLOv5 is primarily a **clone-run repository**, not a normal import-first library. Public workflows use the repository's Python entrypoint names, shared `models/` and `utils/` modules, YAML configs, and checkpoint files. Prefer the bundled references and helper scripts here before reopening repository docs or examples.

## Start Here

- Read `references/repo-provenance.md` before deciding whether this skill matches a checkout or needs refresh.
- Read `references/environment.md` for install, clone-run imports, Python/PyTorch requirements, CUDA, and optional extras.
- Read `references/datasets-and-weights.md` before planning training, validation, downloads, named datasets, or checkpoint use.
- Read `references/model-overview.md` when choosing between detection, segmentation, classification, P6, Hub, or exported runtime formats.
- Read `references/troubleshooting.md` for install/import, optional dependency, data/config, download, device, output, export, and service failures.
- Run `scripts/check_yolov5_env.py --json` for a safe active-environment inspection. It imports modules and checks optional dependencies without downloading models, training, exporting, opening media, or starting a server.

## Route by User Goal

- **Object detection**: use `sub-skills/detection/SKILL.md` for `detect.py`, `train.py`, `val.py`, PyTorch Hub loading, COCO-style datasets, bounding boxes, detection checkpoints, and detection-specific failures.
- **Instance segmentation**: use `sub-skills/segmentation/SKILL.md` for `segment/predict.py`, `segment/train.py`, `segment/val.py`, `*-seg.pt` checkpoints, mask labels, mask output options, and segmentation validation.
- **Image classification**: use `sub-skills/classification/SKILL.md` for `classify/predict.py`, `classify/train.py`, `classify/val.py`, YOLOv5-cls or torchvision classifier models, and ImageFolder/ImageNet-style datasets.
- **Export and benchmarks**: use `sub-skills/export/SKILL.md` for `export.py`, `benchmarks.py`, TorchScript, ONNX, OpenVINO, TensorRT, CoreML, TensorFlow/TFLite/TF.js, Paddle, Edge TPU, dynamic shapes, half precision, and backend prerequisite checks.
- **Flask serving**: use `sub-skills/serving/SKILL.md` for the YOLOv5 Flask REST API pattern, upload validation, API-key behavior, client requests, and safe smoke checks.

## Ordered Handoffs

- New custom detection project: `references/datasets-and-weights.md` → `sub-skills/detection/` → `sub-skills/export/` only after a checkpoint exists.
- Segmentation project: `references/datasets-and-weights.md` → `sub-skills/segmentation/` → `sub-skills/export/` if deployment format conversion is needed.
- Classification project: `sub-skills/classification/` → `references/datasets-and-weights.md` for ImageFolder/named datasets → `sub-skills/export/` for deployment formats.
- REST API service: `sub-skills/serving/` first; route to `sub-skills/detection/` only for model behavior and to `sub-skills/export/` only when the user wants non-PyTorch deployment artifacts.
- Benchmark/export request without a trained checkpoint: first choose or train the task-specific model, then use `sub-skills/export/`.

## Common First Decisions

- **Repository position**: most commands assume the user is acting in a YOLOv5 checkout or has otherwise made the repository modules importable.
- **Task family**: detection uses boxes; segmentation uses boxes plus masks; classification uses class probabilities and ImageFolder-style labels.
- **Weights**: names such as `yolov5s.pt`, `yolov5s-seg.pt`, or `yolov5s-cls.pt` may trigger downloads. Prefer explicit local paths for offline or deterministic work.
- **Datasets**: training/validation commands depend on data YAMLs or ImageFolder directories. Validate dataset paths and class counts before launching expensive runs.
- **Side effects**: prediction, training, validation, export, benchmarks, downloads, and servers can write output directories, fetch files, open streams, or run for a long time. Prefer planner/checker scripts before execution.
- **Optional dependencies**: install export, logging, service, and accelerator packages narrowly for the selected workflow only.
- **Hardware**: CPU is enough for parser/import checks and some tiny workflows, but CUDA is strongly preferred for real training; TensorRT and some half-precision paths require matching GPU/runtime support.

## Safe Baseline

```bash
python - <<'PY'
import torch
import models.common, models.yolo, utils.general
print('torch', torch.__version__)
print('cuda_available', torch.cuda.is_available())
print('yolov5 modules importable')
PY
```

If imports fail, read `references/environment.md` and `references/troubleshooting.md` before changing dependencies.

## Bundled Helpers

- `scripts/check_yolov5_env.py`: safe environment, import, backend, and optional-dependency checker.
- `sub-skills/detection/scripts/plan_detection_command.py`: prints detection train/val/predict command previews with risk warnings.
- `sub-skills/segmentation/scripts/plan_segmentation_command.py`: prints segmentation train/val/predict command previews with mask/data warnings.
- `sub-skills/classification/scripts/plan_classification_command.py`: prints classification train/val/predict command previews with ImageFolder/model warnings.
- `sub-skills/export/scripts/check_export_prereqs.py`: checks optional dependencies for export formats without exporting.
- `sub-skills/serving/scripts/rest_api_smoke.py`: uses a Flask test client and dummy model to verify REST API request validation without downloading weights or starting a server.

## Safety Policy

Do not run downloads, training, validation, prediction on streams, export conversion, benchmarks, notebooks, or long-lived servers until the task has explicit inputs, output locations, runtime budget, and backend expectations. Run original repo tests/examples only as verification after classifying them as safe for the current environment.
