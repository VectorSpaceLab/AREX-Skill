---
name: image-architectures
description: "Routes vit-pytorch 2D image classification backbones,
  architecture-family selection, constructor shape constraints, and image-only
  variant troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# image-architectures

Use this sub-skill when the user wants a `vit-pytorch` model that consumes a regular image tensor shaped `(batch, channels, height, width)` and returns classification logits, or when they need to choose among the 2D architecture zoo.

## Route here for

- Baseline image classifiers: `ViT`, `SimpleViT`, `DeepViT`, `CaiT`, `T2TViT`, and `CCT`.
- Multi-scale or hierarchical 2D image classifiers: `CrossViT`, `PiT`, `LeViT`, `CvT`, `TwinsSVT`, `RegionViT`, `CrossFormer`, `ScalableViT`, `SepViT`, `MaxViT`, `NesT`, `MobileViT`, `XCiT`, `JetViT`, and `ViT-5`.
- Image-only variants: patch dropout, patch merger, small-dataset SPT/LSA, QK-norm, relative projected position bias, specialized CLS, value residual, KEEL post-LN, local/rotary/normalized/look/detection-pooling variants, and `simple_flash_attn_vit` as a PyTorch SDPA-backed image classifier.
- Practical tasks such as selecting a small-memory backbone for `32x32` or `64x64` tensors, repairing `image_size` / `patch_size` divisibility errors, choosing `pool='cls'` vs `pool='mean'`, and keeping README-style examples small enough for CPU smoke checks.

## Route elsewhere

- Variable-resolution image lists, grouped NaViT packing, nested tensors, 1D/3D/N-D tensors, medical/video tensors, or `ViViT`: route to `variable-shapes-video`.
- Distillation, MAE/SimMIM/MPP/MP3/DINO/EsViT and other loss/pretraining/adaptation wrappers: route to `pretraining-and-adaptation`.
- Attention maps, embeddings, hook wrappers, external efficient/custom transformer injection, and Recorder/Extractor usage: route to `introspection-and-customization`.

## First steps for future agents

1. Confirm the input is a fixed-size 4D image batch and the desired output is logits. If the user has variable image sizes, videos, patch-token outputs, or training losses, stop and route as above.
2. Read [references/model-overview.md](references/model-overview.md) to pick a family. Start with `ViT` / `SimpleViT` / `CCT` for baselines, use hierarchical families only when the user needs local windows, convolutional stems, mobile efficiency, or multi-scale structure.
3. Keep constructors tiny until the shape works. For `32x32` or `64x64` tests, use dimensions like `dim=32`, `depth=1`, `heads=2`, `dim_head=16`, `mlp_dim=64`, and small `num_classes`; do not copy large README dimensions unless the user is explicitly benchmarking.
4. Check shape constraints before instantiating: `image_size` and `patch_size` must divide exactly for patch-based families; many hierarchical/window families also require input feature-map sizes divisible by their window or stage settings.
5. For classifier heads, set a positive `num_classes`. In base `ViT`-style classes, `pool='cls'` and `pool='mean'` are the valid pooling choices when that argument exists; many SimpleViT-style and hierarchical classes hard-code mean/global pooling and do not accept `pool`.
6. If a constructor or forward pass fails, read [references/troubleshooting.md](references/troubleshooting.md) before changing families.
7. Use the bundled smoke helper for safe CPU checks: `python scripts/smoke_image_architectures.py --case quick`. It uses reduced random tensors, asserts logits shapes, and never downloads data.

## Bundled runtime files

- [references/model-overview.md](references/model-overview.md) — family table, selection guidance, tiny constructor patterns, and variant import notes.
- [references/troubleshooting.md](references/troubleshooting.md) — repair paths for shape divisibility, pooling, constructor mismatch, memory-heavy defaults, and optional flash-attention branch pitfalls.
- [scripts/smoke_image_architectures.py](scripts/smoke_image_architectures.py) — safe CPU smoke checks for representative 2D image constructors and expected failure cases.
