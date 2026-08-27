---
name: models-and-weights
description: "Select, construct, configure, inspect, and troubleshoot
  TorchVision models, pretrained weights, weight transforms, and feature
  extraction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# TorchVision Models and Weights

Use this sub-skill when a task asks an agent to choose or instantiate a TorchVision model, handle pretrained weights safely, inspect available model/weight APIs, get the correct inference preprocessing, interpret model-family outputs, or extract intermediate features.

## Route Here For

- `torchvision.models` builders and task subpackages: classification, detection, segmentation, video, quantization, optical flow, and feature extraction.
- Model lookup APIs: `list_models`, `get_model`, `get_model_builder`, `get_model_weights`, and `get_weight`.
- `WeightsEnum` objects, `DEFAULT` aliases, `weights.transforms()`, `weights.meta`, download/cache behavior, and no-network test patterns.
- Detection/segmentation/video/optical-flow model output shape interpretation at the model API level.
- `torchvision.models.feature_extraction` node listing and `create_feature_extractor` routing for ResNet/FPN-style backbones.

## Route Elsewhere

- For general augmentation pipelines, v2 transforms, TVTensors, boxes/masks/keypoints metadata, and transform migration, use `../transforms-and-tv-tensors/`.
- For datasets, data roots, image/video decoding, visualization grids, and drawing utilities, use `../datasets-io-utils/`.
- For low-level `torchvision.ops` box/NMS/ROI APIs and custom op diagnostics, use `../ops-and-detection/`.
- For official training/evaluation reference scripts, distributed launches, presets, and long-running recipe commands, use `../training-references/`.

## Fast Paths

- Select or list models: see `references/model-selection.md`.
- Use weights without accidental downloads: see `references/weights-and-inference.md`.
- Extract intermediate features or debug node names: see `references/feature-extraction.md`.
- Diagnose errors and version/cache issues: see `references/troubleshooting.md`.
- Inspect the installed API safely: run `python scripts/inspect_models.py --help`, then `python scripts/inspect_models.py list --include 'resnet*'` or `python scripts/inspect_models.py weights resnet50`.

## Default Safety Policy

Prefer `weights=None` in tests, examples, and smoke checks unless the user explicitly requests pretrained weights and accepts network/cache behavior. Inspect weight metadata and preprocessing with `get_model_weights()` or `get_weight()` before constructing a pretrained model. Call `model.eval()` for inference and use `weights.transforms()` for preprocessing whenever weights are used.
