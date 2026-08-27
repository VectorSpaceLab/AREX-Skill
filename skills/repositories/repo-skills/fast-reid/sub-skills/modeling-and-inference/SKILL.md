---
name: modeling-and-inference
description: "Operate FastReID model registries, safe CPU construction, feature
  extraction, checkpoint loading, and rank utility imports."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# FastReID modeling and inference

Use this sub-skill when the task is about FastReID model construction, backbone/head/meta-architecture registries, CPU-safe forward checks, predictor-style feature extraction, checkpoint expectations, or rank/rerank utility imports.

Route elsewhere when the request is primarily about:

- full training/eval CLI, resume, distributed launch, logs, or benchmark metrics: use `../training-and-evaluation/`.
- dataset registration, person-ID layouts, dataloaders, samplers, or transforms: use `../data-and-datasets/`.
- ONNX/Caffe/TensorRT export, runtime deployment, visualization CLIs, or project extensions: use `../deployment-and-projects/`.
- environment setup, source-only package import, config inheritance, or model-zoo recipe selection: use `../setup-and-configuration/`.

## Operating references and scripts

- `references/model-api.md`: use for builder imports, registry names, model family mapping, config keys, tensor contracts, and layer/head/loss vocabulary.
- `references/inference-workflows.md`: use for CPU dry-runs, DefaultPredictor-style checkpoint loading, demo-style BGR image preprocessing, feature normalization, and rank/rerank utility usage.
- `references/troubleshooting.md`: use to debug missing weights, unwanted ImageNet pretrain downloads, device mismatches, shape errors, rank import mismatches, Cython fallback warnings, and missing OpenCV.
- `scripts/model_forward_smoke.py`: run a no-download CPU model construction and random-tensor forward check; accepts an optional config path and explicit repository source path.
- `scripts/feature_extraction_smoke.py`: run a no-download feature-extraction preprocessing/model smoke; accepts an optional local image, optional local checkpoint, optional config path, and explicit repository source path.

## Safe defaults

- FastReID defaults `MODEL.DEVICE` to `cuda`; the bundled smoke scripts override it to `cpu`.
- Recipe configs often enable `MODEL.BACKBONE.PRETRAIN`; the bundled smoke scripts override it to `False` so they do not download backbone weights.
- Configs may set `MODEL.WEIGHTS`; the feature smoke ignores config weights unless `--weights` is explicitly supplied as a local file.
- Inference tensors are `float32` in `(B, C, H, W)` layout and model outputs are feature tensors in eval mode for standard ReID heads.
- Demo-style image inference starts from OpenCV-style BGR arrays, converts BGR to RGB, resizes to `INPUT.SIZE_TEST`, transposes to CHW, adds a batch dimension, and returns L2-normalized features when requested by the caller.
