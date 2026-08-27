---
name: wiseodd-generative-models
description: "Routes the legacy Generative Models script collection for GAN,
  VAE, RBM, and Helmholtz Machine MNIST workflows, catalog lookup, and
  compatibility troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Unlicense
---

# Generative Models

Use this repo skill for the legacy **Generative Models** script collection: GAN, VAE, RBM, and Helmholtz Machine examples implemented as standalone MNIST training scripts in TensorFlow, PyTorch, and NumPy.

This repository is not an installable Python package and does not expose a CLI. Treat it as a catalog of legacy research scripts plus compatibility guidance for future checkouts of the same repo.

## Quick routing

| User asks for... | Route to |
| --- | --- |
| GAN variants, adversarial losses, WGAN/WGAN-GP, InfoGAN, DiscoGAN, DualGAN, ALI/BiGAN, GibbsNet | `sub-skills/gan/SKILL.md` |
| VAE, CVAE, denoising VAE, adversarial autoencoder, adversarial variational Bayes | `sub-skills/vae/SKILL.md` |
| Binary Restricted Boltzmann Machines, CD vs PCD, Bernoulli visible/hidden units | `sub-skills/rbm/SKILL.md` |
| Binary Helmholtz Machine, wake-sleep algorithm, recognition/generative weights | `sub-skills/helmholtz-machine/SKILL.md` |
| Exact family-to-script catalog, source artifact labels, framework coverage | `references/model-catalog.md` |
| Legacy dependency stack and modern incompatibilities | `references/compatibility.md` |
| Cross-family failures and recovery order | `references/troubleshooting.md` |

## Minimal compatibility check

Run the bundled diagnostic helper before telling a user that an unmodified legacy script will run:

```bash
python scripts/check_legacy_stack.py
```

Use `--strict` when a workflow requires an unchanged script run and warnings should become a failing check. Use `--repo-root <checkout>` only when the user is actively working in a checkout and wants the helper to inspect whether `MNIST_data/` and the expected family directories exist.

For catalog lookup without reopening the source tree, run:

```bash
python scripts/model_catalog.py --family gan
python scripts/model_catalog.py --model wgan-gp
```

## Operating assumptions

- The historical dependency file targets a very old stack: Python 3.5.1-era NumPy/SciPy/scikit-learn/matplotlib plus Keras 1.1.1, while TensorFlow and PyTorch were installed separately.
- Most scripts load MNIST through `tensorflow.examples.tutorials.mnist.input_data`, which is absent from modern TensorFlow 2.x installs.
- Several PyTorch scripts use old scalar logging patterns such as `loss.data[0]`, which fail on modern PyTorch.
- RBM, Helmholtz, and some GAN/VAE scripts use removed NumPy aliases such as `np.float` or `np.int`.
- Generated sample images are expected under an `out/` directory relative to the script's working directory in a source checkout.

## When not to use this skill

- Do not use this skill for modern diffusion, Stable Diffusion, Diffusers, LoRA training, or image-generation services unless the task explicitly compares them with these classic MNIST scripts.
- Do not use it for generic PyTorch/TensorFlow installation help unrelated to this repository's legacy script patterns.
- Do not claim this repository provides packaged import APIs, console entry points, reusable datasets, tests, or production training pipelines.

## Provenance and refresh

Read `references/repo-provenance.md` before deciding whether this skill is current for a new checkout. Refresh the skill if the commit, script inventory, dependency notes, or family layout differs from the provenance snapshot.
