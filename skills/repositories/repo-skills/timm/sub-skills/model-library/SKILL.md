---
name: model-library
description: "Discover timm model names, instantiate models, load pretrained or
  local weights, adapt heads/input channels/pooling, inspect pretrained configs,
  extract features, and debug model registry or weight-loading issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Library

Use this sub-skill when a task asks an agent to choose or instantiate a timm architecture, enumerate available models or pretrained tags, load weights, adapt classification heads or input channels, inspect model defaults, extract feature maps, or troubleshoot model creation and pretrained loading.

## Fast Path

1. Import from the public package surface: `import timm`, then use `timm.list_models`, `timm.list_pretrained`, `timm.get_pretrained_cfg`, and `timm.create_model`.
2. Prefer no-download checks while iterating: `timm.create_model(name, pretrained=False)` and run a small random forward pass.
3. Use `list_models(filter='*resnet*')` for architecture discovery and `list_pretrained(filter='*resnet*')` for exact `architecture.tag` pretrained identifiers.
4. Create a model with the exact signature from timm 1.0.28.dev0: `create_model(model_name, pretrained=False, pretrained_cfg=None, pretrained_cfg_overlay=None, checkpoint_path=None, cache_dir=None, scriptable=None, exportable=None, no_jit=None, **kwargs)`.
5. Adapt common dimensions at construction time: `num_classes`, `in_chans`, `global_pool`, `features_only`, `out_indices`, `output_stride`, `scriptable`, `exportable`, and `no_jit`.
6. Inspect `model.pretrained_cfg` or `timm.get_pretrained_cfg(model_name).to_dict()` before choosing transforms, class counts, input channels, or cache/download behavior.

## Decision Guide

- Need model discovery or exact API signatures: read `references/api-reference.md`.
- Need classifier/input/pooling/feature-extraction recipes: read `references/model-workflows.md`.
- Need to diagnose unknown names, tag failures, cache/auth/download problems, checkpoint mismatches, or feature shape surprises: read `references/troubleshooting.md`.
- Need a safe local smoke test without network access: run `python sub-skills/model-library/scripts/model_smoke_check.py --model resnet18 --num-classes 7` from the skill root or copy the script into a project.

## Boundary Routing

- Use `../data-pipelines/` for transforms, loaders, `resolve_data_config`, augmentation, and preprocessing pipelines after reading `pretrained_cfg` here.
- Use `../training-workflows/` for optimizers, schedulers, losses, training loops, fine-tuning scripts, and distributed training.
- Use `../export-and-interoperability/` for ONNX, TorchScript export flows, checkpoint conversion tools, Hugging Face push/pull packaging, and deployment formats.
- Use `../layers-and-components/` for low-level timm layers, blocks, activations, pooling modules, and component internals.

## Guardrails

- Do not set `pretrained=True` in smoke checks unless downloads, cache location, and Hugging Face authentication are expected and acceptable.
- Do not assume all names returned by `list_models()` have pretrained weights; use `list_pretrained()` or `is_model_pretrained()` when weights matter.
- Do not hardcode image normalization, crop size, or class count for pretrained models; inspect `pretrained_cfg` and route preprocessing details to `data-pipelines`.
- Do not assume `features_only=True` returns the same number of feature levels for every model family; inspect `model.feature_info.channels()` and `model.feature_info.reduction()`.
