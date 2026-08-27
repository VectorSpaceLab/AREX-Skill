---
name: pytorch-vae
description: "Routes PyTorch-VAE tasks to config-driven training and model API
  workflows for the collection of variational autoencoders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PyTorch-VAE

Use this skill for the repository that collects many PyTorch variational autoencoder variants, their configs, and their smoke tests.

Two routes matter most:

- **Training/config route** for experiment runs, CelebA data layout, TensorBoard logs, checkpoints, and trainer settings.
- **Model-reference route** for constructor arguments, forward/loss behavior, sampling, generation, and registry lookups.

## Start here

- Read `references/repo-provenance.md` when you need to check whether this skill still matches the current checkout.
- Read `references/model-overview.md` when you need a fast model-family map.
- Read `references/troubleshooting.md` for cross-cutting install, backend, config, and runtime failures.
- Open `sub-skills/training/SKILL.md` for config-driven fitting and data/logging questions.
- Open `sub-skills/model-reference/SKILL.md` for class signatures, latent-shape details, or synthetic smoke checks.

## Install

From a PyTorch-VAE checkout, install the runtime stack with a CUDA-capable torch/torchvision pair, then the repo requirements:

```bash
python -m pip install 'pip<24.1' 'numpy<2' 'setuptools<70' six
python -m pip install 'torch==1.13.1+cu117' 'torchvision==0.14.1+cu117' --extra-index-url https://download.pytorch.org/whl/cu117
python -m pip install -r requirements.txt
```

If you are using a different CUDA wheel tag, keep the torch and torchvision versions matched.

## Verified baseline

The repo was inspected with a CUDA-capable Python 3.10 environment using:

- torch 1.13.1+cu117
- torchvision 0.14.1+cu117
- pytorch-lightning 1.5.6
- PyYAML 6.0
- torchsummary 1.5.1
- tensorboard 2.21.0
- numpy 1.26.4
- setuptools 69.5.1
- six 1.17.0

That baseline was verified on an NVIDIA A100 host with CUDA 11.7 available.

## Route map

### Training / config-driven experiments
Use this route when the user wants to choose a config, run or dry-run a training job, validate CelebA data layout, inspect logging output, or troubleshoot trainer arguments.

Helpful bundled entry point:

- `sub-skills/training/scripts/train_from_config.py` — validates a config from any checkout root and can run a full fit only when `--fit` is set.

Read `sub-skills/training/references/workflows.md` before a real training run.

### Model reference / smoke testing
Use this route when the user wants to instantiate a model class, compare constructor kwargs, run a tiny forward/loss check, or test sample/generate behavior for a specific architecture.

Helpful bundled entry point:

- `sub-skills/model-reference/scripts/model_smoke.py` — instantiates a model from a config, runs synthetic forward/loss checks, and can optionally exercise sample/generate paths.

Read `sub-skills/model-reference/references/api-reference.md` when you need exact signatures or special-case model behavior.

## Minimal check

From the generated skill directory, point the bundled helpers at the checkout you want to inspect and run the smallest smoke that matches the task.

- Training dry-run: `python ./sub-skills/training/scripts/train_from_config.py --repo-root /path/to/PyTorch-VAE --config /path/to/PyTorch-VAE/configs/vae.yaml`
- Model smoke: `python ./sub-skills/model-reference/scripts/model_smoke.py --repo-root /path/to/PyTorch-VAE --config /path/to/PyTorch-VAE/configs/vae.yaml`

Use `--fit` only when you actually want the full training loop.

## Common guardrails

- This repo is source-first; it does not expose a packaged install entry point.
- Full training is GPU-oriented and expects the Lightning 1.x API used by the repo code.
- Some model families have special inputs or sample behavior. Read the model-reference route before guessing labels, latent sizes, or sample availability.
- If a config or model name is not in the registry, stop and inspect the bundled references instead of guessing.
