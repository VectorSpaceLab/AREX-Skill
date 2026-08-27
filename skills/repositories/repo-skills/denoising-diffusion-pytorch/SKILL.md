---
name: denoising-diffusion-pytorch
description: "Use denoising-diffusion-pytorch for PyTorch DDPM/DDIM image
  diffusion, 1D sequence diffusion, conditioning and guidance, and advanced
  diffusion variants."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# denoising-diffusion-pytorch

Use this repo skill when a Researcher needs to operate the public `denoising-diffusion-pytorch` package (`denoising_diffusion_pytorch` import) from self-contained guidance. It covers the inspected public API surface at version 2.3.1.

## Install and sanity check

```bash
python -m pip install denoising-diffusion-pytorch
python - <<'PYCODE'
from denoising_diffusion_pytorch import Unet, GaussianDiffusion, Unet1D, GaussianDiffusion1D
print('denoising_diffusion_pytorch imports ok')
PYCODE
```

For a no-training environment check, run [scripts/check_env.py](scripts/check_env.py). It verifies package metadata, public imports, a tiny CPU tensor operation, and optional CUDA visibility.

## Route by task

| User task | Read |
| --- | --- |
| 2D image DDPM/DDIM, `Unet`, `GaussianDiffusion`, image folder `Trainer`, FID, RePaint/inpainting, image tensor shape errors | [sub-skills/image-diffusion/SKILL.md](sub-skills/image-diffusion/SKILL.md) |
| 1D/time-series/sequence tensors, `Unet1D`, `GaussianDiffusion1D`, `Dataset1D`, `Trainer1D`, channel-first vs channel-last layout | [sub-skills/sequence-diffusion/SKILL.md](sub-skills/sequence-diffusion/SKILL.md) |
| classifier-free guidance, class labels, `cond_scale`, CFG++, external classifier `cond_fn`, `XMWrapper` multi-candidate loss | [sub-skills/conditioning-guidance/SKILL.md](sub-skills/conditioning-guidance/SKILL.md) |
| Karras UNets, video-shaped Karras 3D, continuous-time / v-param / EDM / simple diffusion, learned variance, weighted objective, flash/SDPA compatibility | [sub-skills/advanced-variants/SKILL.md](sub-skills/advanced-variants/SKILL.md) |

## Shared references

- [references/package-overview.md](references/package-overview.md) maps public exports, dependencies, and sub-skill ownership.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting install/import, PyTorch/CUDA, Accelerate, optional FID, and smoke-test failures.
- [references/repo-provenance.md](references/repo-provenance.md) records the source snapshot and refresh baseline.

## Operating rules

- Use the bundled scripts for smoke tests; do not run long training or FID for routine verification.
- Keep data tensors normalized to `[0, 1]` unless `auto_normalize=False` is explicitly chosen.
- CPU is the default verification backend; CUDA, flash attention, FID, and Accelerate multi-GPU are optional accelerators unless a user explicitly asks for them.
- The package has no public CLI entry points. Workflows are Python API workflows.
- If a task asks to edit this repository rather than use the package, this repo skill can explain APIs, but repository-maintenance policy is outside the selected operating graph.
