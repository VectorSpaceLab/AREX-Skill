---
name: cnn-model-building
description: "Build CPU-safe PyTorch CNN layers and model helpers with MMCV
  builders, module bundles, wrappers, plugins, transformers, and complexity
  utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMCV CNN Model Building

Use this sub-skill when a task needs MMCV's PyTorch-dependent CNN construction helpers: config-style layer builders, `ConvModule`, depthwise separable blocks, wrapper layers, plugin blocks, transformer bricks, model complexity checks, or small ResNet/VGG helper layers.

Do not use this sub-skill for compiled CUDA/C++ ops installation or `mmcv.ops` runtime failures; route those to `ops-and-builds`. Do not use it for image preprocessing or data transforms; route those to `media-processing` or `data-transforms`.

## Quick Workflow

1. Confirm `torch` and `mmcv` import before using `mmcv.cnn`; MMCV Lite can build pure PyTorch CNN layers but does not provide compiled `mmcv._ext` ops.
2. Choose the smallest builder: `build_conv_layer`, `build_norm_layer`, `build_activation_layer`, `build_padding_layer`, `build_upsample_layer`, or `build_plugin_layer`.
3. Prefer `ConvModule` for conv/norm/activation bundles and explicitly set `norm_cfg`, `act_cfg`, `bias`, and `order` when matching existing PyTorch behavior.
4. Use `DepthwiseSeparableConvModule`, `ContextBlock`, `NonLocal*`, `Scale`, wrappers, `fuse_conv_bn`, and `get_model_complexity_info` only where their assumptions match the model.
5. For custom layers, register with `mmengine.registry.MODELS` before building from config.
6. Run the bundled smoke helper after edits or environment changes:

```bash
python scripts/cnn_builder_smoke.py
```

## References

- [API Reference](references/api-reference.md): builder signatures, supported config `type` values, return conventions, and module parameters.
- [Workflows](references/workflows.md): recipes for layer configs, `ConvModule` migration, registry extension, fusion, complexity, and CPU-safe transformer bricks.
- [Troubleshooting](references/troubleshooting.md): common config, torch, registry, shape, bias, order, plugin, and optional-ops failures.
