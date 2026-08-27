# FCOS Model Overview for Inference

## High-level API models

The public `FCOS` class has a small built-in model catalog. Use these keys for `FCOS(model_name=...)`:

| API key | Intended use | Notes |
| --- | --- | --- |
| `fcos_R_50_FPN_1x` | Baseline ResNet-50 FPN FCOS detector | Uses a pretrained weight URL and per-class thresholds. |
| `fcos_syncbn_bs32_c128_MNV2_FPN_1x` | Lighter MobileNetV2 FPN detector | Used by the installed `fcos` script with `nms_thresh=0.6`; better for quick demos. |

## Config/weight model zoo

The repo documents additional configs and weights for ResNet, ResNeXt, deformable-conv, and MobileNet variants. Those are best handled as config/weight pairs through the training/evaluation sub-skill rather than directly through `FCOS(model_name=...)`.

Representative config families:

- Improved ResNet-50/101 FPN: `fcos_imprv_R_50_FPN_1x`, `fcos_imprv_R_101_FPN_2x`.
- Deformable-conv variants: names containing `dcnv2`; require compiled deformable convolution support.
- ResNeXt variants: names containing `X_101`.
- MobileNetV2 variants: names containing `MNV2`, including SyncBN and smaller tower channel options.

## Choosing a model

- Use `fcos_syncbn_bs32_c128_MNV2_FPN_1x` for a quick installed CLI demo when speed and lower memory matter more than maximum AP.
- Use improved ResNet-50 configs for a common accuracy/speed baseline.
- Use `dcnv2` or ResNeXt configs only when the extension/CUDA stack is known good.
- For CPU-only smoke checks, avoid constructing large models unless weights are already available and runtime cost is acceptable.
