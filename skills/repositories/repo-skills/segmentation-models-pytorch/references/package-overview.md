# Package Overview

## Purpose

Use this reference for the broad shape of the `segmentation_models_pytorch` package before choosing a focused sub-skill.

## Public Package Shape

- Distribution name: `segmentation_models_pytorch`; public import: `segmentation_models_pytorch`.
- Runtime package requirement from metadata: Python `>=3.10`.
- Core dependency families: PyTorch/TorchVision, timm, Hugging Face Hub, safetensors, NumPy, Pillow, and tqdm.
- Public task domain: semantic segmentation models with encoder-decoder architectures, pretrained backbones, losses, metrics, and deployment-friendly save/load/export paths.

## Architecture Families

SMP exposes these public architecture routes at the package root and through `smp.create_model`:

- U-Net family: `Unet`, `UnetPlusPlus`, `MAnet`, `Linknet`.
- Pyramid/scene parsing family: `FPN`, `PSPNet`, `PAN`, `UPerNet`.
- Atrous/deeplab family: `DeepLabV3`, `DeepLabV3Plus`.
- Transformer-heavy families: `Segformer`, `DPT`.

Read `sub-skills/model-building/SKILL.md` for constructor parameters, output shapes, auxiliary classification heads, and smoke checks.

## Encoder And Preprocessing Surface

SMP separates model architecture from encoder/backbone choice. Native/ported encoders live in the registry returned by `smp.encoders.get_encoder_names()`, while timm universal encoders use `tu-` names. Pretrained weights can require network/cache access; `encoder_weights=None` is the safest offline construction default.

Read `sub-skills/encoders-preprocessing/SKILL.md` for encoder selection, `tu-` naming, DPT-compatible backbones, and preprocessing parameter behavior.

## Training And Evaluation Surface

SMP losses and metrics are mode-sensitive. Binary, multiclass, and multilabel segmentation expect different logit and target shapes. Most losses default to `from_logits=True`, while metrics generally use `smp.metrics.get_stats(...)` to build true/false positive/negative tensors before applying a score reduction.

Read `sub-skills/training-evaluation/SKILL.md` for loss/metric recipes, tensor shape validation, and safe training loop skeletons.

## Persistence And Export Surface

SMP model instances support `save_pretrained(...)`; the package root exposes `from_pretrained(...)`. Local save/load is safe for smoke tests. Hugging Face Hub sharing requires network and credentials. Export workflows depend on PyTorch, model architecture, encoder behavior, and optional packages such as ONNX.

Read `sub-skills/model-export/SKILL.md` for persistence, changed class counts, Hub boundaries, and export readiness checks.

## Repository Maintenance Surface

When working in an SMP checkout, changes usually affect one or more of these surfaces:

- `segmentation_models_pytorch/decoders/` for model families.
- `segmentation_models_pytorch/encoders/` for backbone registries and preprocessing metadata.
- `segmentation_models_pytorch/losses/` and `segmentation_models_pytorch/metrics/` for training/evaluation behavior.
- `docs/`, `tests/`, `misc/`, and `Makefile` for documentation, focused tests, and generated tables.

Read `sub-skills/repo-development/SKILL.md` for maintainer-focused routing and test selection.
