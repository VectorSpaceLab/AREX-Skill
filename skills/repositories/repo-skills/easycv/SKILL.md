---
name: easycv
description: "Routes EasyCV training, evaluation, prediction, export, and data workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# EasyCV

Use this skill for EasyCV workflows that sit on top of the repo's configuration-driven model zoo, training / evaluation entry points, predictor APIs, data-preparation helpers, and export or optimization paths.

EasyCV is a broad computer-vision toolbox. Keep this root router short and use the focused sub-skills for workflow detail.

## Start here

- Read `references/installation.md` if you need the public install path, optional extras, or a minimal smoke check.
- Read `references/model-zoo-overview.md` when you need to choose a config family or understand the main task coverage.
- Read `references/cli-reference.md` when you need the canonical command/module front doors.
- Read `references/troubleshooting.md` for cross-cutting install, import, backend, config, and OSS issues.
- Run `scripts/check_easycv_env.py` to confirm the package import surface and optional backend availability in a prepared environment.

## Route map

### `sub-skills/data-preparation/`
Use for dataset layouts, annotation conversion, file/OSS I/O, dataset download prep, and repo-maintained conversion helpers.

Typical asks:
- "How do I prepare COCO/ImageNet/VOC/nuScenes data for EasyCV?"
- "How do I convert annotations or check a data layout?"
- "How do I use EasyCV file I/O with local or OSS paths?"

### `sub-skills/training-and-evaluation/`
Use for training, fine-tuning, evaluation, config selection, distributed launch, metric setup, and training-time logging or visualization.

Typical asks:
- "How do I train a classification or detection model?"
- "Which config template should I start from?"
- "How do I run eval or resume a checkpoint?"

### `sub-skills/prediction-and-inference/`
Use for Python predictor APIs, batch prediction, feature extraction, OCR / pose / video / segmentation inference, and exported-model consumption.

Typical asks:
- "How do I run batch inference on images or tables?"
- "Which predictor class should I use?"
- "How do I load a JIT / Blade / ONNX / raw checkpoint for inference?"

### `sub-skills/export-and-optimization/`
Use for model export, JIT / Blade / ONNX packaging, pruning, quantization, TorchAccelerator, and other inference-optimization paths.

Typical asks:
- "How do I export a checkpoint for inference?"
- "How do I prune or quantize a YOLOX model?"
- "What extra packages are needed for Blade or TorchAcc?"

## What this skill does not do

- It does not depend on the original checkout remaining available at runtime.
- It does not expose generated-skill content outside the router and bundled references.
- It does not import optional heavyweight extras unless the selected workflow needs them.

## Common entry points

The installed package exposes the public workflow modules under `easycv.tools` and the main APIs under `easycv.apis` and `easycv.predictors`.

Use those modules when you want to stay in the installed package rather than the source checkout.

## Shared guardrails

- Match the config family to the task before editing paths or hyperparameters.
- Prefer the smallest runnable command first: `--help`, import checks, or a tiny smoke input.
- Treat advanced backends such as `easy_predict`, `modelscope`, `pai_nni`, `blade_compression`, `torchacc`, or `nvidia-dali` as optional dependencies unless the selected workflow needs them.
- Keep dataset conversion and optimization helpers separate from core training and inference guidance.
