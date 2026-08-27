---
name: model-reference
description: "Explains PyTorch-VAE model constructors, registry lookups,
  latent-shape conventions, and synthetic forward/loss/sample checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Reference

Use this sub-skill when the user wants to choose a model, inspect constructor arguments, compare variants, or run a tiny synthetic smoke on one architecture.
It covers the shared registry, special kwargs, forward/loss outputs, and sample/generate caveats.
The bundled command examples assume the generated skill directory is the current working directory.

## Read first

- `references/api-reference.md` for constructor signatures and model-specific notes.
- `references/troubleshooting.md` for labels, sample availability, and pretrained-feature pitfalls.
- `scripts/model_smoke.py` for the bundled synthetic forward/loss/sampling helper.
- `../../references/model-overview.md` when you only need a quick family map.

## Include here

- Looking up a model name in `models.vae_models`.
- Understanding constructor kwargs such as `latent_dim`, `num_samples`, `categorical_dim`, `embedding_dim`, `latent1_dim`, and `latent2_dim`.
- Checking how a model's `forward()` result maps to `loss_function()` inputs.
- Knowing which models expect labels, multiple optimizers, or sample/generate flags.
- Running a tiny synthetic smoke against a selected model.

## Exclude or route elsewhere

- Experiment orchestration, `data_params`, and checkpoint/logging setup -> `sub-skills/training/SKILL.md`.
- Full training jobs -> training.
- Repo provenance and staleness -> `references/repo-provenance.md`.

## Typical triggers

- "what constructor does BetaTCVAE take"
- "how do I call sample on ConditionalVAE"
- "what kwargs does VQVAE need"
- "why does forward return extra tensors"
- "which models have generate()"
- "run a quick smoke for DFCVAE"

## Workflow

1. Read the API reference to identify the exact class and kwargs.
2. Use the model smoke script with a small batch and the repo root you want to inspect.
3. If a model expects labels or a special optimizer index, follow the model-specific notes in the API reference before guessing.
4. If the model smoke fails because the model needs CUDA, network downloads, or a missing optional dependency, check the troubleshooting page before retrying.

## Hand off to training when needed

If the user switches from "how do I instantiate this model" to "how do I run the experiment", route to the training sub-skill instead.
