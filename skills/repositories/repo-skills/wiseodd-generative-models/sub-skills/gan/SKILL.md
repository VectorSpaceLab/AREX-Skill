---
name: gan
description: "Routes legacy GAN-family MNIST scripts, framework choices, model
  variant lookup, and TensorFlow/PyTorch compatibility troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Unlicense
---

# GAN

Use this sub-skill for GAN-family requests in the Generative Models repository: vanilla GAN, conditional GAN, InfoGAN, WGAN, WGAN-GP, LSGAN, ACGAN, BEGAN, BGAN, EBGAN, f-GAN, GAP, DiscoGAN, DualGAN, COGAN, ALI/BiGAN, MAGAN, Softmax GAN, GibbsNet, and mode-regularized GAN.

## Route here when

- The user asks which GAN variant or source artifact label matches a modeling goal.
- The user needs TensorFlow-vs-PyTorch guidance for a legacy GAN example.
- The user asks about GAN sample outputs, MNIST assumptions, or why a GAN script fails on a modern stack.
- The user names WGAN-GP, InfoGAN, DiscoGAN, DualGAN, ALI/BiGAN, GibbsNet, or another GAN variant from the catalog.

## Route elsewhere when

- VAE / CVAE / AAE / AVB: `../vae/SKILL.md`
- Binary RBM CD/PCD: `../rbm/SKILL.md`
- Helmholtz Machine wake-sleep: `../helmholtz-machine/SKILL.md`
- Shared catalog, provenance, and compatibility: `../../SKILL.md`

## Fast decisions

- Default GAN baseline: vanilla GAN.
- Class-conditioned generation: conditional GAN or ACGAN.
- Wasserstein objective with gradient penalty: WGAN-GP, TensorFlow-only in this repo.
- Image-to-image / domain translation style examples: DiscoGAN, DualGAN, or COGAN.
- Bidirectional inference: ALI/BiGAN or GibbsNet.
- Mode-collapse or divergence variants: mode-regularized GAN, MAGAN, f-GAN, LSGAN, Softmax GAN, BGAN, BEGAN, or EBGAN.

## Read next

- `references/workflows.md` for the full GAN variant map and framework coverage.
- `references/troubleshooting.md` for GAN-specific modern-stack failures.
- `../../references/model-catalog.md` for the repo-wide source artifact catalog.
- `../../references/compatibility.md` for the shared TensorFlow/PyTorch/NumPy compatibility matrix.
- `../../scripts/check_legacy_stack.py` before claiming an unchanged GAN example can execute.
