---
name: yolox
description: "Use YOLOX for object-detection inference, training/data
  experiments, and checkpoint export/deployment workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# YOLOX

Use this repo skill when a task involves YOLOX, anchor-free YOLO object detection, YOLOX model selection, PyTorch inference, custom-data training/evaluation, experiment files, checkpoints, ONNX/TorchScript export, or optional deployment runtimes.

YOLOX is a PyTorch object-detection package. This skill is self-contained operating guidance for the versioned package surface; it does not require the original repository checkout.

## Start here

1. Read [references/installation-and-environment.md](references/installation-and-environment.md) when installing YOLOX, checking imports, choosing CPU/CUDA dependencies, or deciding which optional export/deployment packages are needed.
2. Run [scripts/check_yolox_install.py](scripts/check_yolox_install.py) for a safe package/API/backend smoke check before expensive work.
3. Route to a sub-skill:
   - [sub-skills/inference-and-api/SKILL.md](sub-skills/inference-and-api/SKILL.md) for PyTorch image/video/webcam inference, model selection, checkpoint loading, preprocessing/postprocessing, visualization, and inference API diagnostics.
   - [sub-skills/training-and-data/SKILL.md](sub-skills/training-and-data/SKILL.md) for custom datasets, `Exp` files, training/evaluation commands, caching, image-size settings, freezing, assignment visualization, and loggers.
   - [sub-skills/export-and-deployment/SKILL.md](sub-skills/export-and-deployment/SKILL.md) for ONNX/TorchScript export and optional ONNXRuntime, TensorRT, OpenVINO, ncnn, MegEngine, or nebullvm deployment choices.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when the failure spans installation, imports, optional dependencies, CUDA, checkpoints, or routing between sub-skills.
5. Read [references/repo-provenance.md](references/repo-provenance.md) only when you need the source version, evidence paths, or staleness baseline for this generated skill.

## Quick route map

| User intent | Route | First action |
|---|---|---|
| Run YOLOX on images/video/webcam | `inference-and-api` | Choose `--name` for built-ins or `--exp-file` for custom models; validate install with the inference smoke helper. |
| Use the Python API in an app | `inference-and-api` | Follow the distilled `get_exp` → `get_model` → `ValTransform` → forward → `postprocess` → `vis` flow. |
| Train on COCO/VOC/custom data | `training-and-data` | Inspect the `Exp`, dataset root, annotations, class count, and image sizes before launching training. |
| Evaluate or resume a checkpoint | `training-and-data` | Match checkpoint, `Exp`, dataset/evaluator, device count, and resume-vs-fine-tune mode. |
| Export a checkpoint to ONNX/TorchScript | `export-and-deployment` | Dry-run the bundled export helper, then export with an explicit checkpoint path. |
| Use TensorRT/OpenVINO/ncnn/MegEngine/nebullvm | `export-and-deployment` | Treat these as optional stacks; probe SDK/toolchain/runtime availability before claiming support. |
| Install/import/debug YOLOX | root references | Run `scripts/check_yolox_install.py`, then use root troubleshooting and the nearest sub-skill. |

## Minimal install smoke

After installing YOLOX and required dependencies in the target environment:

```bash
python scripts/check_yolox_install.py --name yolox-nano --device auto --test-size 64
```

Use CPU for portable diagnostics:

```bash
python scripts/check_yolox_install.py --name yolox-nano --device cpu --test-size 64
```

The smoke check builds a model and can probe CUDA, but it does not download weights, read datasets, run training, or prove detection accuracy.

## Operating boundaries

- Use package/module commands such as `python -m yolox.tools.demo`, `python -m yolox.tools.train`, and `python -m yolox.tools.eval` when the installed package exposes them. Do not rely on source checkout script paths.
- Full inference needs a checkpoint that matches the selected `Exp`; full training/evaluation needs datasets and usually CUDA resources.
- ONNX and TorchScript export require a trained checkpoint. TensorRT/OpenVINO/ncnn/MegEngine/nebullvm require extra runtime/toolchain packages not covered by the base install.
- Old weights that require `--legacy` in PyTorch demo/eval are not supported by current deployment demos; use a compatible old YOLOX version for those deployment paths or regenerate weights.

## Avoid when

- The task is general object-detection theory with no YOLOX usage, configuration, or package workflow.
- The task targets a different YOLO implementation such as YOLOv5/YOLOv8/Ultralytics unless the user is explicitly migrating to or comparing with YOLOX.
- The user asks for a long benchmark or full training run without providing data, checkpoints, compute budget, and permission.
