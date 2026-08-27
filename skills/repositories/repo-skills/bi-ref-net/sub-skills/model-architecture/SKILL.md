---
name: model-architecture
description: "Route BiRefNet model construction, architecture, backbone,
  checkpoint, and export questions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# BiRefNet Model Architecture Router

Use this sub-skill when the task is about constructing or loading BiRefNet models, matching weights to the right backbone/configuration, cleaning checkpoint keys, understanding decoder/backbone flags, or planning ONNX/export work.

## Fast routing

- For model APIs, local checkpoint loading, Hugging Face loading choices, `image2patches`/`patches2image`, and `check_state_dict`, read [references/api-reference.md](references/api-reference.md).
- For backbone names, decoder flags, configuration-to-weight compatibility, and model-zoo matching, read [references/backbones-and-architecture.md](references/backbones-and-architecture.md).
- For ONNX, deformable convolution export, runtime providers, opset, and memory caveats, read [references/onnx-and-export-notes.md](references/onnx-and-export-notes.md).
- For common model, state-dict, Hugging Face, backbone-weight, ONNX, and memory failures, read [references/troubleshooting.md](references/troubleshooting.md).
- To run a safe local probe without downloads, use [scripts/birefnet_model_probe.py](scripts/birefnet_model_probe.py).

## Boundary with sibling sub-skills

- Route image-directory inference, masks, foreground refinement, alpha/comparison outputs, device autocast, and video postprocessing to `../inference-and-postprocessing/SKILL.md`.
- Route dataset layout, `Config` data fields, task/testset/training-set selection, and custom data validation to `../configuration-and-data/SKILL.md`.
- Route training launches, resume epochs, checkpoint schedules, evaluation metrics, and best-checkpoint selection to `../training-and-evaluation/SKILL.md`.

## Default safe stance

Prefer `BiRefNet(bb_pretrained=False)` when loading a full BiRefNet checkpoint, then apply `check_state_dict` before `load_state_dict`. Use `bb_pretrained=True` only when intentionally initializing a new model with backbone weights and the configured backbone-weight files or torchvision/timm weights are available. Treat Hugging Face and ONNX flows as asset/backend-dependent unless the model cache, optional packages, and hardware/provider have been explicitly checked.

## Recommended operating flow

1. Identify the loading path: source constructor, source `from_pretrained`, Transformers `AutoModelForImageSegmentation`, or local `.pth` checkpoint.
2. Confirm the backbone family and configuration fields before diagnosing tensor-size mismatches; default `config.bb` is `swin_v1_l`, while lite/tiny weights need matching config choices.
3. Run `scripts/birefnet_model_probe.py --repo-root <checkout> --json` when a source checkout is available; add `--construct-model` only when dependency imports and memory are acceptable.
4. For local checkpoints, clean `module.` and `_orig_mod.` prefixes before `load_state_dict`, then only treat remaining errors as true architecture mismatches.
5. For ONNX/export tasks, read the export notes before installing optional packages or cloning external exporter code.

## Done criteria

- The chosen weight source, backbone, and config flags are compatible.
- The user knows whether pretrained backbone files, Hugging Face cache/network, or optional packages are required.
- State-dict prefix cleanup has been attempted before changing model architecture.
- ONNX/deployment plans include provider, opset, deformable-convolution, and memory constraints.
