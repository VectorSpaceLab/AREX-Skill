---
name: damo-yolo
description: "Training, inference, and deployment workflows for DAMO-YOLO object detection."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# DAMO-YOLO

Use this repo skill for DAMO-YOLO object detection workflows built around the installed `damo` package. The main user-facing routes are training, demo inference, and deployment/export. This skill is self-contained: it bundles the reusable launchers, references, and smoke checks future agents need without reopening the original repository checkout.

## Start here

1. Install or verify the `damo` package in the active environment. For a local checkout, the usual command is `pip install -e .` because the package metadata reads `requirements.txt` and installs the `damo` distribution from this source tree.
2. Run `scripts/check_model_smoke.py --config <config.py> --workdir <dir>` when you need a quick import/model/config sanity check before a longer workflow.
3. Read `references/workflows.md` for the route map and bundled helper scripts.
4. Read `references/troubleshooting.md` if the task involves a missing dependency, config mismatch, class-count error, or relative-path failure.
5. Read `references/model-overview.md` and `references/api-reference.md` when you need architecture or API details that are not obvious from the sub-skill router.

## Route map

### `training`
Use for training, fine-tuning, resume, evaluation, teacher-student distillation, custom COCO dataset setup, config editing, and distributed CUDA/NCCL launch commands.

Read:
- `sub-skills/training/SKILL.md`
- `sub-skills/training/references/training-workflows.md`
- `sub-skills/training/references/custom-coco-datasets.md`
- `sub-skills/training/references/config-editing.md`
- `sub-skills/training/references/troubleshooting.md`

Bundled helpers:
- `sub-skills/training/scripts/launch_train.sh`
- `sub-skills/training/scripts/launch_eval.sh`
- `sub-skills/training/scripts/validate_coco_config.py`

### `inference`
Use for image, video, and camera demo inference with Torch, ONNX, or TensorRT engines, including engine selection and visualization behavior.

Read:
- `sub-skills/inference/SKILL.md`
- `sub-skills/inference/references/engine-and-data-flow.md`
- `sub-skills/inference/references/demo-workflows.md`
- `sub-skills/inference/references/source-decisions.md`
- `sub-skills/inference/references/troubleshooting.md`

Bundled helper:
- `sub-skills/inference/scripts/damo_yolo_safe_demo.py`

### `deployment`
Use for ONNX export, TensorRT export/evaluation planning, partial INT8 quantization guidance, and deployment backend readiness checks.

Read:
- `sub-skills/deployment/SKILL.md`
- `sub-skills/deployment/references/workflows.md`
- `sub-skills/deployment/references/cli-reference.md`
- `sub-skills/deployment/references/source-decisions.md`
- `sub-skills/deployment/references/troubleshooting.md`

Bundled helpers:
- `sub-skills/deployment/scripts/check_deploy_env.py`
- `sub-skills/deployment/scripts/export_onnx_safe.py`

## Routing cues

- If the prompt says train, fine-tune, resume, evaluate, distill, or prepare a COCO dataset, choose `training`.
- If the prompt says demo, image, video, camera, OpenCV visualization, Torch engine, ONNX Runtime, or TensorRT inference, choose `inference`.
- If the prompt says export, ONNX, TensorRT, engine build, partial quantization, ONNX Runtime NMS, or backend dependency check, choose `deployment`.
- If the prompt is only asking whether the environment, package install, config file, or model shape is sane before a long run, use `scripts/check_model_smoke.py` plus the relevant sub-skill.

## Core constraints to remember

- COCO-style datasets are expected by the training pipeline; dataset names must contain `coco`.
- `cfg.dataset.class_names` and `cfg.model.head.num_classes` must agree.
- Relative TinyNAS structure reads need `--workdir` or absolute config paths.
- `Config.merge()` only handles exact top-level keys reliably; prefer edited config files for nested changes.
- Training and evaluation require CUDA/NCCL.
- Torch-based inference can fall back to CPU, but ONNX Runtime and TensorRT still depend on their own optional runtimes.
- TensorRT and partial INT8 quantization are optional backend paths; do not claim them unless the active environment actually provides the required packages and libraries.
