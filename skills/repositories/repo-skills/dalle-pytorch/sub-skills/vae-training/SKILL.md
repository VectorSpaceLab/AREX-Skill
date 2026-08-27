---
name: vae-training
description: "Train and inspect DALLE-pytorch discrete VAE workflows, VAE
  checkpoints, and pretrained VAE alternatives."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# VAE training

Use this sub-skill when the user asks about `DiscreteVAE`, VAE codebooks, VAE image folders, VAE checkpoint files, OpenAI's pretrained VAE, Taming Transformers VQGAN, or the VAE stage before DALL-E transformer training.

## Read first

- `references/workflows.md` for VAE API recipes, command construction, checkpoint contents, and pretrained VAE choices.
- `references/troubleshooting.md` for image-size assertions, OpenAI VAE torch limits, W&B/GPU side effects, and VQGAN path errors.
- `scripts/tiny_vae_api_smoke.py` when you need a no-download CPU check.
- `scripts/build_train_vae_command.py` when a user needs a reproducible VAE training command template.

## Typical routes

| Request | Action |
| --- | --- |
| "Train the VAE" or "prepare `vae.pt`" | Validate image folder shape, build a command with `scripts/build_train_vae_command.py`, and warn about CUDA/W&B/checkpoint side effects before running long training. |
| "Use `DiscreteVAE` in Python" | Use the API recipe in `references/workflows.md`; verify with `scripts/tiny_vae_api_smoke.py`. |
| "OpenAI pretrained VAE fails" | Check torch version; source asserts torch `<=1.10`. Prefer a trained `DiscreteVAE` or `VQGanVAE` unless the user accepts a legacy environment. |
| "Use VQGAN VAE" | Require both model checkpoint and YAML config paths when not using the default download path; route backend/download questions to root troubleshooting. |
| "What is in `vae.pt`?" | Explain `hparams` and `weights`, and that DALL-E training reconstructs `DiscreteVAE(**hparams)` before loading weights. |

## Minimal API pattern

```python
import torch
from dalle_pytorch import DiscreteVAE

vae = DiscreteVAE(
    image_size=256,
    num_layers=3,
    num_tokens=8192,
    codebook_dim=512,
    hidden_dim=64,
    num_resnet_blocks=1,
)
images = torch.randn(4, 3, 256, 256)
loss = vae(images, return_loss=True)
loss.backward()
indices = vae.get_codebook_indices(images)
recon = vae.decode(indices)
```

Keep detailed constructor notes and training command options in `references/workflows.md`, not in this router.

## Boundary notes

- DALL-E transformer training after VAE preparation belongs to `../dalle-training/SKILL.md`.
- Image generation and CLIP ranking belong to `../generation-and-ranking/SKILL.md`.
- DeepSpeed/Apex/Horovod/Docker/CUDA setup belongs to `../distributed-and-backends/SKILL.md`.
- Do not instantiate pretrained VAE wrappers merely to inspect the package; they can download model files or assert on torch version.

## Validation checklist

Before approving a VAE workflow answer:

- image size is a power of two and matches the intended downstream DALL-E VAE;
- image mode (`RGB` vs transparent `RGBA`) matches `channels`;
- checkpoint side effects and output filenames are explicit;
- W&B/account/network behavior is acknowledged;
- if a full script command is produced, the user has a checkout or script copy that can run it;
- package-level API alternatives are offered for pip-only users.
