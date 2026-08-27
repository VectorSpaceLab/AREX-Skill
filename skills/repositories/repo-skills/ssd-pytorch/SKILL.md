---
name: ssd-pytorch
description: "Operate the amdegroot SSD.PyTorch repository for SSD300 model
  construction, VOC/COCO training, evaluation, and demos."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# ssd-pytorch

Use this repo skill when a task names `ssd.pytorch`, `SSD.PyTorch`, `amdegroot/ssd.pytorch`, or asks for the legacy PyTorch SSD300 object detector implementation, its VOC/COCO training pipeline, evaluation scripts, or demos.

## What this skill covers

- SSD300 model construction with `build_ssd(phase, size=300, num_classes=21)`.
- Prior boxes, VGG/extras/multibox heads, detection decode, and NMS behavior.
- VOC and COCO dataset layout, annotation transforms, SSD augmentations, and `detection_collate`.
- Training command planning for `train.py`, including base VGG weights, checkpoints, CUDA, and Visdom.
- VOC evaluation/test-output command planning with `eval.py` and `test.py`.
- Notebook and webcam demo prerequisites.
- Legacy-runtime troubleshooting for modern Python, modern PyTorch, import-time COCO label-map behavior, and optional dependencies.

## Start here

1. Read [references/installation-and-compatibility.md](references/installation-and-compatibility.md) before running code. This repository has no package metadata and has known legacy compatibility traps.
2. Check [references/repo-provenance.md](references/repo-provenance.md) when freshness matters; it records the source commit, branch, and evidence paths used to build this skill.
3. Use [scripts/smoke_imports.py](scripts/smoke_imports.py) for a no-download import/model smoke check in the user's current environment.
4. Route to the focused sub-skill:
   - [sub-skills/model-inference/SKILL.md](sub-skills/model-inference/SKILL.md) for model construction, priors, box utilities, weights, and inference-layer compatibility.
   - [sub-skills/data-training/SKILL.md](sub-skills/data-training/SKILL.md) for VOC/COCO layouts, augmentation, dataloaders, and training command planning.
   - [sub-skills/evaluation-demos/SKILL.md](sub-skills/evaluation-demos/SKILL.md) for VOC mAP/test-output planning, notebook demos, and webcam prerequisites.
4. If the symptom spans setup, model, data, and scripts, first read [references/troubleshooting.md](references/troubleshooting.md), then follow its route.

## Minimal operating context

SSD.PyTorch is a source-layout project, not a modern installable Python package. Future agents usually need one of these contexts:

- a checkout or copied source tree on `PYTHONPATH`, or
- an environment where modules such as `ssd`, `data`, `layers`, and `utils` are importable.

Core dependencies for selected workflows are PyTorch, TorchVision, NumPy, OpenCV (`cv2`), and Pillow for `test.py` image imports. Optional dependencies include `pycocotools` for COCO, `visdom` for training plots, `imutils` for the webcam demo, and Jupyter/IPython for notebook use.

## High-priority caveats

- Importing the package-level `data` module can fail if the default COCO label map is absent, because `COCOAnnotationTransform()` is evaluated during module import. See [references/troubleshooting.md](references/troubleshooting.md).
- `build_ssd('test')` may construct under modern PyTorch but fail on forward because `Detect` is an old-style `torch.autograd.Function`. Use [sub-skills/model-inference](sub-skills/model-inference/SKILL.md) before promising end-to-end inference or evaluation.
- Full training, full VOC mAP evaluation, dataset downloads, weight downloads, webcam loops, and notebook demos are not safe smoke tests. Plan and validate prerequisites before running them.
- The repository is SSD300-focused. `size=512` config tables are empty in source and should not be treated as implemented.

## Typical routes

| User task | Route |
|---|---|
| "Build SSD300 for VOC and inspect output shapes" | `model-inference`, then `scripts/inspect_model_shapes.py` |
| "Why does `build_ssd('test')` fail on PyTorch 2?" | `model-inference/references/troubleshooting.md` |
| "Prepare VOC0712 for training" | `data-training`, then `scripts/validate_dataset_layout.py --dataset voc` |
| "Create a COCO training command" | `data-training/references/training-workflow.md`, then `scripts/plan_training_command.py --dataset COCO` |
| "Run or plan VOC mAP evaluation" | `evaluation-demos/references/evaluation-and-test.md`, then `scripts/plan_evaluation_command.py --mode eval` |
| "Check webcam demo dependencies" | `evaluation-demos`, then `scripts/check_demo_requirements.py` |

## Verification stance

This skill is based on source, README, live import inspection, and safe smoke checks. It intentionally does not claim reproduced README mAP, full training completion, dataset download success, webcam access, or notebook execution. Those require external data, weights, hardware, and runtime choices in a Researcher session.
