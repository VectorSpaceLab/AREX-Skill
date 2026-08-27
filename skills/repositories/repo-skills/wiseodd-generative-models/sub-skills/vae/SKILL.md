---
name: vae
description: "Routes legacy VAE-family MNIST scripts, backend choices, model
  variant lookup, and TensorFlow/PyTorch compatibility troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Unlicense
---

# VAE

Use this sub-skill for VAE-family requests in the Generative Models repository: vanilla VAE, conditional VAE, denoising VAE, adversarial autoencoder, and adversarial variational Bayes.

## Route here when

- The user asks which VAE variant or source artifact label matches a modeling goal.
- The user needs TensorFlow-vs-PyTorch guidance for a legacy VAE example.
- The user asks about MNIST inputs, generated image outputs, latent-variable assumptions, or why a VAE script fails on a modern stack.
- The user names CVAE, DVAE, AAE, or AVB.

## Route elsewhere when

- GAN variants: `../gan/SKILL.md`
- Binary RBM CD/PCD: `../rbm/SKILL.md`
- Helmholtz Machine wake-sleep: `../helmholtz-machine/SKILL.md`
- Shared catalog, provenance, and compatibility: `../../SKILL.md`

## Fast decisions

- Default VAE baseline: vanilla VAE.
- Class-conditioned generation: conditional VAE.
- Denoising / corrupted input reconstruction: denoising VAE.
- Adversarial latent regularization: adversarial autoencoder.
- Adversarial variational objective with a T network: adversarial variational Bayes.

## Shared conventions

- These are standalone legacy MNIST training loops, not a packaged library or CLI.
- The TensorFlow branches use old placeholder/session style.
- The PyTorch branches still rely on the legacy TensorFlow MNIST loader and old scalar logging patterns.
- Sample images are written to a working-directory-local `out/` directory in source checkouts.

## Read next

- `references/workflows.md` for the full VAE variant map and framework coverage.
- `references/troubleshooting.md` for VAE-specific modern-stack failures.
- `../../references/model-catalog.md` for the repo-wide source artifact catalog.
- `../../references/compatibility.md` for the shared TensorFlow/PyTorch/NumPy compatibility matrix.
- `../../scripts/check_legacy_stack.py` before claiming an unchanged VAE example can execute.
