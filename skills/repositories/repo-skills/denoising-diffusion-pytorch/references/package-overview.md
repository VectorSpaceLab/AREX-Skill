# Package Overview

## Purpose

Read this to choose the correct denoising-diffusion-pytorch route and to understand package-wide dependencies and backend assumptions.

## Public package facts

- Distribution: `denoising-diffusion-pytorch`
- Import package: `denoising_diffusion_pytorch`
- Inspected version: `2.3.1`
- Python requirement: `>=3.8`
- Runtime dependencies from package metadata: `accelerate`, `einops`, `ema-pytorch>=0.4.2`, `numpy`, `pillow`, `pytorch-fid`, `scipy`, `torch>=2.0`, `torchvision`, `tqdm`.
- Public CLI entry points: none discovered.

## Root exports

```python
from denoising_diffusion_pytorch import (
    Unet, GaussianDiffusion, Trainer,
    LearnedGaussianDiffusion, ContinuousTimeGaussianDiffusion,
    WeightedObjectiveGaussianDiffusion, ElucidatedDiffusion,
    VParamContinuousTimeGaussianDiffusion,
    Unet1D, GaussianDiffusion1D, Trainer1D, Dataset1D,
    KarrasUnet, KarrasUnet1D, KarrasUnet3D, InvSqrtDecayLRSched,
    XMWrapper,
)
```

Additional module-level imports used by the sub-skills:

```python
from denoising_diffusion_pytorch.denoising_diffusion_pytorch import Dataset
from denoising_diffusion_pytorch.classifier_free_guidance import Unet as CFGUnet, GaussianDiffusion as CFGGaussianDiffusion
from denoising_diffusion_pytorch.guided_diffusion import Unet as GuidedUnet, GaussianDiffusion as GuidedGaussianDiffusion
from denoising_diffusion_pytorch.repaint import Unet as RePaintUnet, GaussianDiffusion as RePaintGaussianDiffusion
from denoising_diffusion_pytorch.simple_diffusion import UViT, GaussianDiffusion as SimpleGaussianDiffusion
```

## Capability ownership

| Capability | Owner |
| --- | --- |
| Root import, package version, PyTorch/CUDA sanity | `scripts/check_env.py` and this root skill |
| 2D image loss, sample, interpolation, image folder trainer, FID, RePaint | `image-diffusion` |
| 1D sequence diffusion, layout, `Dataset1D`, `Trainer1D` | `sequence-diffusion` |
| CFG class labels, external classifier guidance, XM multi-candidate loss | `conditioning-guidance` |
| Karras, continuous-time, EDM, simple diffusion, learned/weighted objectives, SDPA/flash | `advanced-variants` |

## Backend policy

The required default backend is CPU PyTorch. The inspected environment also passed a CUDA allocation smoke, but every required selected workflow has a safe CPU substitute. Treat CUDA, flash attention, and multi-GPU behavior as optional unless a user explicitly asks to validate accelerator performance.
