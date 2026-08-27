---
name: vit-pytorch
description: "Routes vit-pytorch Vision Transformer model construction,
  variable-resolution and video inputs, pretraining wrappers, attention
  introspection, and package troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# vit-pytorch

Use this repo skill when a task names `vit-pytorch`, `vit_pytorch`, lucidrains' Vision Transformer package, or a model/workflow implemented by that package: `ViT`, `SimpleViT`, `NaViT`, `ViViT`, `CCT`, `CrossViT`, `MAE`, `Dino`, `Recorder`, `Extractor`, and related image/video transformer variants.

## Quick setup and import check

Install the public package in the user's Python environment:

```bash
pip install vit-pytorch
```

Then run a minimal import/forward check:

```python
import torch
from vit_pytorch import ViT

model = ViT(image_size=32, patch_size=8, num_classes=7,
            dim=32, depth=1, heads=2, dim_head=16, mlp_dim=64)
logits = model(torch.randn(2, 3, 32, 32))
assert logits.shape == (2, 7)
```

For a broader package health check, run the bundled helper after installing the package:

```bash
python scripts/check_vit_pytorch_install.py --run-smoke
```

The package exposes Python modules only; no console CLI entry points were found in this snapshot.

## Route by user intent

- **Fixed-size 2D image classifier or architecture choice**: read [sub-skills/image-architectures/SKILL.md](sub-skills/image-architectures/SKILL.md). Use it for plain `ViT` / `SimpleViT`, CCT, CrossViT, PiT, LeViT, CvT, MaxViT, XCiT, JetViT, ViT-5, and image-only variants such as patch dropout or patch merger.
- **Variable-resolution images, NaViT grouping, 1D/3D/N-D tensors, or video**: read [sub-skills/variable-shapes-video/SKILL.md](sub-skills/variable-shapes-video/SKILL.md). Use it for `NaViT`, nested tensor variants, `vit_3d`, `simple_vit_3d`, `cct_3d`, `ViViT`, 1D models, N-D models, and video wrappers.
- **Loss wrappers, pretraining, distillation, adaptation, or fine-tuning**: read [sub-skills/pretraining-and-adaptation/SKILL.md](sub-skills/pretraining-and-adaptation/SKILL.md). Use it for `DistillWrapper`, MAE, SimMIM, MPP, MP3, DINO, EsViT, Learnable Memory ViT, LeJEPA, VAT, VAAT, WWT, and decorrelation auxiliary loss.
- **Attention maps, embeddings, hooks, efficient/custom transformer injection, or performance wrappers**: read [sub-skills/introspection-and-customization/SKILL.md](sub-skills/introspection-and-customization/SKILL.md). Use it for `Recorder`, `Extractor`, `efficient.ViT`, `parallel_vit`, and `simple_flash_attn_vit`.

## Operating rules

1. Identify the user's tensor layout before choosing a route: image `(batch, channels, height, width)`, NaViT image lists `(channels, height, width)`, video `(batch, channels, frames, height, width)`, 1D `(batch, channels, seq_len)`, or N-D `(batch, channels, *input_shape)`.
2. Start with tiny random tensors and small constructor dimensions before copying README-scale examples. Most helper scripts use `dim=32`, `depth=1`, and CPU-safe tensors to validate shape and wrapper wiring.
3. Treat optional dependencies as workflow-specific. `torch`, `torchvision`, and `einops` are base dependencies; `torchaudio` is needed for VAAT, while Accelerate, W&B, Kaggle data, external transformer packages, or checkpoints belong only to explicit full-training or research-idea requests.
4. Do not run dataset downloads, notebooks, long training loops, or checkpoint loaders as default smoke checks. Use the bundled helpers first, then ask for data/runtime approval if the user requests full training.
5. If a workflow fails, read [references/troubleshooting.md](references/troubleshooting.md) and the nearest sub-skill troubleshooting reference before changing packages or model families.
6. If working against a live checkout rather than an installed release, read [references/repo-provenance.md](references/repo-provenance.md) to decide whether this skill should be refreshed.

## Shared references and scripts

- [references/api-reference.md](references/api-reference.md) — top-level package facts, important exports, verified signatures, and optional dependency notes.
- [references/troubleshooting.md](references/troubleshooting.md) — cross-cutting install/import, backend, optional dependency, and version-fragile wrapper guidance.
- [references/repo-provenance.md](references/repo-provenance.md) — source snapshot and refresh baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) — structured routing metadata for managed repo-skill import.
- [scripts/check_vit_pytorch_install.py](scripts/check_vit_pytorch_install.py) — package import, metadata, optional module, and minimal forward smoke checks.
