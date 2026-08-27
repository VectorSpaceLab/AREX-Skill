# VAE Workflow Map

This page is the detailed decision table for the VAE family. The root skill stays router-like; use this page for the exact file mapping and backend choice.

## How to choose
1. Pick the family by modeling need.
2. Pick the backend by environment.
3. In a source checkout, the family directory is the expected working directory so `../../MNIST_data` resolves and `out/` lands locally.

## Family / script map

| Modeling need | Family folder | TensorFlow script | PyTorch script | Notes |
| --- | --- | --- | --- | --- |
| Plain unsupervised VAE | `vanilla_vae` | `VAE/vanilla_vae/vae_tensorflow.py` | `VAE/vanilla_vae/vae_pytorch.py` | canonical ELBO VAE on MNIST |
| Class-conditioned VAE | `conditional_vae` | `VAE/conditional_vae/cvae_tensorflow.py` | `VAE/conditional_vae/cvae_pytorch.py` | uses labels to condition generation |
| Denoising VAE | `denoising_vae` | `VAE/denoising_vae/dvae_tensorflow.py` | `VAE/denoising_vae/dvae_pytorch.py` | reconstructs from corrupted inputs |
| Adversarial autoencoder | `adversarial_autoencoder` | `VAE/adversarial_autoencoder/aae_tensorflow.py` | `VAE/adversarial_autoencoder/aae_pytorch.py` | adds a latent-space discriminator |
| Adversarial variational Bayes | `adversarial_vb` | `VAE/adversarial_vb/avb_tensorflow.py` | `VAE/adversarial_vb/avb_pytorch.py` | uses the Q/P/T adversarial setup |

## Backend choice

Both branches are legacy scripts and both still rely on the TensorFlow MNIST loader.

| If you need... | Prefer... | Why |
| --- | --- | --- |
| Original TensorFlow 1.x placeholder/session style | TensorFlow | matches the script shape already in the repo |
| A PyTorch implementation of the same VAE family | PyTorch | keeps the model/training code in torch while still using the same MNIST source |
| The least code churn on a modern stack | Neither unmodified | both branches need compatibility fixes before they run cleanly today |

## Input and output conventions

- MNIST path: every script calls `input_data.read_data_sets('../../MNIST_data', one_hot=True)`.
- Working directory: in a source checkout, the family folder—not the repo root—is the expected launch point so `../../MNIST_data` resolves correctly.
- Output path: every script writes sample images to a local `out/` directory created on demand.
- Filename pattern: generated images are zero-padded PNGs such as `out/000.png`, `out/001.png`, and so on.
- No CLI: there are no command-line flags, config files, or packaged entry points in this repo.

## Family-specific notes

- Vanilla VAE: best default when the user only wants a standard MNIST VAE.
- CVAE: use when the user needs class control or wants to condition on labels.
- DVAE: use when the user wants robustness to corrupted input.
- AAE: use when the user wants adversarial latent regularization rather than a plain KL term.
- AVB: use when the user wants the adversarial variational Bayes formulation.

## Cross-links

- Root catalog: `../../../references/model-catalog.md`
- Root compatibility: `../../../references/compatibility.md`
- Root troubleshooting: `../../../references/troubleshooting.md`
- Family troubleshooting: `troubleshooting.md`
