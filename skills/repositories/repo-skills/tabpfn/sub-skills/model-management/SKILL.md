---
name: model-management
description: "Guides TabPFN model downloads, authentication, cache behavior,
  save/load persistence, checkpoint conversion, visualization, and SageMaker
  references."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TabPFN model management

Use this sub-skill when the user is working with checkpoint files, cache
locations, browser/token access, fitted-model persistence, or the repository's
checkpoint conversion and visualization helpers.

## Start here

- Read `references/model-overview.md` for versions, path resolution, and download sources.
- Read `references/model-weights.md` for auth, cache, and offline behavior.
- Read `references/checkpoint-utilities.md` for `.ckpt`, `.safetensors`, and `.tabpfn_fit` workflows.
- Read `references/visualization.md` for regression-distribution plotting.
- Read `references/sagemaker.md` only if the user explicitly asks about the endpoint template.
- Read `references/troubleshooting.md` for access, cache, and checkpoint failures.
- Run `scripts/download_models.py --help` or `scripts/convert_checkpoint_to_safetensors.py --help` for safe local helpers.

## Use this sub-skill when

- The task is about model downloads, cache directories, or browser/token authentication.
- The user wants to save or load a fitted TabPFN estimator.
- The user wants to convert a checkpoint to SafeTensors.
- The user wants to plot a regression distribution from `output_type="full"`.
- The user wants a reference for the SageMaker endpoint example.

## Route elsewhere

- Ordinary estimator use and outputs: `../tabular-prediction/SKILL.md`.
- Data cleaning, category detection, or config fields: `../preprocessing-config/SKILL.md`.
- Batched scoring and cache/performance behavior: `../batched-performance/SKILL.md`.
- Tuning, differentiable input, or fine-tuning: `../tuning-and-advanced/SKILL.md`.

## What this route owns

- Model version selection and default checkpoint resolution.
- Browser/token access and local auth cache behavior.
- Download planning and offline cache recovery.
- Fitted-model save/load round trips.
- Checkpoint format conversion and visualization helpers.

## What to remember

- First-use model access may require license acceptance.
- `TABPFN_MODEL_CACHE_DIR` and `TABPFN_MODEL_CACHE_SIZE` change cache behavior.
- `save_fitted_tabpfn_model` writes fitted estimator state, not a new foundation model.
- The SageMaker example is a template around an existing endpoint, not a default local workflow.
