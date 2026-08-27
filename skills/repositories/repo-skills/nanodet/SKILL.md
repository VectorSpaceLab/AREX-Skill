---
name: "nanodet"
description: "Routes NanoDet users to dataset/config, training/evaluation, and
  inference/export workflows for the NanoDet object-detection repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# NanoDet

NanoDet is a lightweight, config-driven object-detection toolkit. Use this repo skill when you need to inspect configs, prepare datasets, train or evaluate models, run inference, or export models for deployment.

## Start here

- Read `references/api-reference.md` for the verified builders, dataset constructors, training task, and utility APIs.
- Read `references/model-overview.md` when you need the supported backbone / neck / head / loss combinations.
- Read `references/troubleshooting.md` when installation, config loading, checkpoint loading, or export fails.
- Read `references/repo-provenance.md` when you want to check whether this skill matches the current repository snapshot or before refreshing it.

## Install and import

The repository was verified with a CPU-only PyTorch stack on Python 3.8.
The package name and import root are both `nanodet`.

1. Install a compatible PyTorch / torchvision pair first.
2. Install the repo requirements and `timm`.
3. Install the repo in editable mode.

Example:

```bash
python -m pip install torch==1.13.1+cpu torchvision==0.14.1+cpu -f https://download.pytorch.org/whl/torch_stable.html
python -m pip install pytorch-lightning<2.0 timm pycocotools onnx onnx-simplifier onnxruntime opencv-python pyaml tensorboard matplotlib imagesize termcolor tqdm pytest
python -m pip install -e .
python -I -c "import nanodet, torch; print(nanodet.__version__, torch.__version__)"
```

If you want a quick sanity check of the installed package, run `scripts/check_install.py` from this skill tree.

## Route map

### `dataset-config`
Use this route for YAML config inspection, dataset format questions, preprocessing pipelines, and config-driven model assembly.

Read:
- `sub-skills/dataset-config/SKILL.md`
- `sub-skills/dataset-config/references/configuration.md`
- `sub-skills/dataset-config/references/data-formats.md`

Typical tasks:
- Validate a config file before training.
- Check a COCO, XML, or YOLO dataset layout.
- Understand `class_names`, `input_size`, `keep_ratio`, `multi_scale`, or pipeline settings.

### `training`
Use this route for training, validation, test-time evaluation, checkpoint loading, EMA, logging, optimizer settings, and multiprocessing behavior.

Read:
- `sub-skills/training/SKILL.md`
- `sub-skills/training/references/workflows.md`
- `sub-skills/training/references/troubleshooting.md`

Typical tasks:
- Launch or debug training and validation.
- Resume from a checkpoint or convert an old checkpoint.
- Inspect the Lightning task, logger, evaluator, or optimizer behavior.

### `inference-export`
Use this route for image/video/webcam inference, ONNX export, TorchScript export, RepVGG deploy conversion, FLOPs inspection, and deployment notes.

Read:
- `sub-skills/inference-export/SKILL.md`
- `sub-skills/inference-export/references/workflows.md`
- `sub-skills/inference-export/references/deployment.md`
- `sub-skills/inference-export/references/troubleshooting.md`

Typical tasks:
- Run a demo on an image, video, or webcam.
- Export a checkpoint for ONNX or TorchScript consumers.
- Prepare RepVGG models for deployment backends.

## Shared runtime helpers

- `scripts/check_install.py` — verify the package import surface and optional runtime dependencies.
- `scripts/check_install.py --config <config.yml>` — optionally build a model from a config as a quick smoke check.

## Notes

- The selected extraction scope is CPU-first because the verified native candidates are CPU-safe.
- CUDA is supported by the repository docs, but it is optional for this generated skill unless a later task explicitly asks for it.
- Keep all runtime links inside this skill tree; do not depend on the original repository checkout at runtime.
