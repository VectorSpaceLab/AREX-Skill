---
name: rf-detr
description: "Use and maintain RF-DETR for real-time object detection, instance
  segmentation, keypoint preview, training, export, deployment, and repository
  development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RF-DETR Repo Skill

Use this skill when a task involves the `rfdetr` Python package or the RF-DETR repository: selecting model variants, running prediction, fine-tuning on COCO/YOLO/keypoint datasets, exporting artifacts, deploying to inference runtimes, or editing the RF-DETR source tree.

RF-DETR is a PyTorch/DINOv2-based real-time vision model family for object detection, instance segmentation, and keypoint preview. The public package name is `rfdetr` and the default concrete detection model for new examples is `RFDETRSmall` / `"rfdetr-small"`.

## Install and smoke-check first

For ordinary package use:

```bash
pip install rfdetr
python -c "from rfdetr import RFDETRSmall; print(RFDETRSmall.size)"
```

Add extras only for the workflow you need:

```bash
pip install "rfdetr[train,cli]"       # training and Lightning CLI
pip install "rfdetr[augment]"         # Albumentations / Kornia augmentation backends
pip install "rfdetr[onnx]"            # ONNX export and ONNX Runtime inspection
pip install "rfdetr[tensorrt]"        # TensorRT export on NVIDIA GPU hosts
pip install "rfdetr[tflite]"          # experimental TFLite export
pip install "rfdetr[executorch]"      # experimental ExecuTorch export
pip install "rfdetr[coreml]"          # native CoreML export on supported macOS hosts
pip install "rfdetr[plus]"            # Plus detection models; separate package/license
```

Run the bundled read-only environment check when import, optional dependency, CLI, or backend readiness is unclear:

```bash
python scripts/check_rfdetr_environment.py
python scripts/check_rfdetr_environment.py --extras train onnx augment --check-cuda
```

## Route by task

| User task | Open |
| --- | --- |
| Choose an RF-DETR model class/alias, run image/video/stream prediction, load checkpoints, interpret `supervision` detections/keypoints, fix labels/devices/shape/downloads | [sub-skills/inference-and-models/SKILL.md](sub-skills/inference-and-models/SKILL.md) |
| Fine-tune/evaluate detection, segmentation, or keypoint models; validate COCO/YOLO/keypoint datasets; use `rfdetr` Lightning CLI and YAML configs; debug resume, DDP, augmentation, loggers | [sub-skills/training-and-cli/SKILL.md](sub-skills/training-and-cli/SKILL.md) |
| Export to ONNX, TensorRT, TFLite, ExecuTorch, or CoreML; choose deployment artifacts; diagnose optional backend constraints and output naming | [sub-skills/export-and-deployment/SKILL.md](sub-skills/export-and-deployment/SKILL.md) |
| Modify RF-DETR source, tests, docs, configs, package metadata, CI, or examples while following repository contribution rules | [sub-skills/repository-development/SKILL.md](sub-skills/repository-development/SKILL.md) |

## Shared references

- Read [references/model-overview.md](references/model-overview.md) when you need the released model families, default class choices, alias rules, license boundaries, and task-to-model map.
- Read [references/optional-dependencies-and-backends.md](references/optional-dependencies-and-backends.md) before installing extras, choosing CPU/GPU/mobile export dependencies, or explaining an unavailable backend.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, optional dependency, data/config, checkpoint, CUDA, and workflow failures before drilling into a sub-skill-specific troubleshooting file.
- Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this generated skill is stale for a checkout or before refreshing it.

## Core decisions to preserve

1. Default new detection examples to `RFDETRSmall` / `"rfdetr-small"`; treat `RFDETRBase` / `"rfdetr-base"` as deprecated for new examples, docs, and tests.
2. Use released sized segmentation classes (`RFDETRSegNano`, `RFDETRSegSmall`, `RFDETRSegMedium`, `RFDETRSegLarge`, `RFDETRSegXLarge`, `RFDETRSeg2XLarge`); do not use `RFDETRSegPreview` for new work.
3. Use preview variants only when the capability has no released sized version. In current RF-DETR evidence, keypoints are preview-only: `RFDETRKeypointPreview` / `"rfdetr-keypoint-preview"`.
4. Keep optional backend claims honest. A CPU import check does not verify TensorRT, CoreML, ExecuTorch QNN, XLA, or CUDA-specific behavior.
5. Prefer bundled scripts in this skill for inspection and preflight checks. They are designed to be safe, read-only, and runnable without downloading pretrained weights or starting training.

## Common first-response patterns

- For an inference question, ask for the task family (detection, segmentation, keypoint), checkpoint source if any, input type, and whether the user needs CPU, CUDA, or deployment-runtime constraints.
- For a training question, validate dataset layout before recommending a long run, then choose model family, extras, batch/effective-batch plan, resume semantics, and evaluation split.
- For an export question, start with ONNX unless the target runtime requires another artifact. Reject invalid static combinations early, especially `dynamic_batch=True` for ExecuTorch/CoreML or QNN without `soc`.
- For repository changes, follow RF-DETR TDD and style rules, choose focused tests by changed paths, and run full pre-commit before handoff.
