---
name: layers-and-components
description: "Use timm reusable layers, classifier heads, pooling,
  normalization, attention/drop modules, patch embeddings, and
  feature-extraction wrappers when building or validating custom models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Layers and Components

Use this sub-skill when a task asks an agent to assemble custom timm-style model pieces, validate tensor shapes through reusable layers, replace classifier heads or pooling, configure normalization/activation/drop modules, use `PatchEmbed`, or wrap a model for feature extraction.

## Fast Path

1. Import from the current public layer surface: `from timm.layers import PatchEmbed, ClassifierHead, SelectAdaptivePool2d, DropPath`.
2. Validate tensor layout before wiring components: most convolutional layers consume `NCHW`; `PatchEmbed(flatten=True)` returns `NLC`; `PatchEmbed(output_fmt='NHWC')` returns channel-last spatial output.
3. Use `ClassifierHead(in_features, num_classes, pool_type='avg')` for NCHW feature maps and set `num_classes=0` when the caller wants pre-classifier features.
4. Use `SelectAdaptivePool2d(pool_type='avg'|'max'|'avgmax'|'catavgmax', flatten=True)` when a custom head needs global pooling; remember `catavgmax` doubles channels.
5. Use `features_only=True`, `out_indices`, `output_stride`, and `model.feature_info` for normal backbone feature maps; use `forward_intermediates()` only for families that expose it.
6. Run `python sub-skills/layers-and-components/scripts/layer_component_probe.py` from the skill root, or copy it into a project, for a no-download component shape smoke check.

## Decision Guide

- Need import names, constructor patterns, output shapes, and layout notes: read `references/layers-api.md`.
- Need recipes for custom blocks, patch embeddings, classifier heads, and feature wrappers: read `references/custom-model-components.md`.
- Need to debug shape, dtype, train/eval, feature extraction, FX tracing, or moved-import issues: read `references/troubleshooting.md`.
- Need architecture discovery, `create_model`, pretrained configs, or model registry behavior: route to `../model-library/`.
- Need data transforms or loaders around model inputs: route to `../data-pipelines/`.
- Need training loops, losses, schedulers, or stochastic-depth schedules in a full run: route to `../training-workflows/`.

## Guardrails

- Prefer `timm.layers` imports; `timm.models.layers` is a deprecated compatibility path.
- Do not assume all feature wrappers work with arbitrary custom models; provide `feature_info` with `num_chs`, `reduction`, and `module` when wrapping your own network.
- Do not mix `NCHW`, `NHWC`, and `NLC` silently; choose the component's `input_fmt`/`output_fmt` explicitly when leaving the default layout.
- Do not test components with `pretrained=True`; reusable layer validation should work on random tensors without downloads.
