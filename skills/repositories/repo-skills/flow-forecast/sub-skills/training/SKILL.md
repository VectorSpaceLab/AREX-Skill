---
name: training
description: "Repository operating skill for Flow Forecast config-driven
  training, validation, checkpoints, model selection, and light smoke runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Training

Use this sub-skill when the task is about fitting, resuming, validating, or debugging Flow Forecast models. It covers the JSON trainer workflow, meta/autoencoder training, loss and optimizer selection, and the data-loader/model-contract details that determine whether a run can start successfully.

Start with:

- [../../references/model-overview.md](../../references/model-overview.md) for the package-wide registry when you need the exact model, loss, optimizer, or scaler name.
- [references/configuration.md](references/configuration.md) for the top-level config shape.
- [references/model-configs.md](references/model-configs.md) for model-family-specific parameter requirements.
- [references/losses-and-optimizers.md](references/losses-and-optimizers.md) for registry names and loss caveats.
- [references/workflows.md](references/workflows.md) for the standard fit/resume and NARX smoke paths.
- [references/troubleshooting.md](references/troubleshooting.md) for the most common training-time failures.
- [scripts/validate_training_config.py](scripts/validate_training_config.py) before any long run.
- [scripts/narx_smoke.py](scripts/narx_smoke.py) for a tiny end-to-end NARX sanity check.

## What This Sub-skill Covers

- `python -m flood_forecast.trainer -p config.json` for the main PyTorch and DA-RNN entry path.
- `python -m flood_forecast.meta_train -p config.json` for the autoencoder/meta path.
- `PyTorchForecast`, `train_transformer_style`, `torch_single_train`, `compute_validation`, and `EarlyStopper`.
- The `model_dict_function` registry, `scaling_function`, `make_criterion_functions`, and `weight_path` / `weight_path_add` transfer-learning knobs.
- DA-RNN as a Python-level training workflow using `flood_forecast.da_rnn.train_da`, not a standalone package CLI; read the troubleshooting caveat before using `preprocess_da_rnn.make_data` output directly.

## What Belongs Elsewhere

- CSV cleaning, interpolation, datetime normalization, and series grouping belong in [data-preparation](../data-preparation/SKILL.md).
- Saved-model rollout, inference, evaluation, and plots belong in [inference](../inference/SKILL.md).
- Catchment encoders, contrastive pretraining, CrossViViT, Neural ODEs, and GR4 hybrid hydrology belong in [multimodal-physics](../multimodal-physics/SKILL.md).

## Typical Workflow

1. Validate the config with `scripts/validate_training_config.py`.
2. Check the model registry and loader contract in `references/model-configs.md` and `references/configuration.md`.
3. Make sure the data-loader class, forecast windows, and loss function match the model family.
4. Run the smallest safe training path first, usually CPU-only and often with one epoch on a tiny fixture.
5. Only then scale up to the real dataset or accelerator-backed run.

## Operating Notes

1. For forecasting models, `inference_params` should usually be present because the trainer evaluates after fitting.
2. `wandb` must be `False` or a mapping; a bare `True` is not valid because the code reads `wandb.get(...)`.
3. `device: "auto"` prefers CUDA, then MPS, then CPU. Explicit `cuda` or `mps` requests fail if the backend is missing.
4. JSON `scaler_params` are often written with `feature_range` as a list; the trainer normalizes that to a tuple before constructing the scaler.
5. `GeneralClassificationLoader` and `VariableSequenceLength` follow different validation paths from forecasting loaders, so do not expect the same post-training evaluation flow.

## Shared References And Scripts

- [references/configuration.md](references/configuration.md): top-level config keys, required dataset/training blocks, and loader-specific fields.
- [references/model-configs.md](references/model-configs.md): extra shape and parameter requirements for NARX, temporal models, DA-RNN, AE/meta, and ODE/hybrid models.
- [references/losses-and-optimizers.md](references/losses-and-optimizers.md): criterion, optimizer, scaler, and interpolation registries.
- [references/troubleshooting.md](references/troubleshooting.md): registry errors, loss explosions, WandB issues, and config mismatch recovery.
- [scripts/validate_training_config.py](scripts/validate_training_config.py): syntax, registry, and contract validation.
- [scripts/narx_smoke.py](scripts/narx_smoke.py): tiny synthetic NARX fit/infer path for smoke checks.

## Non-goals

- Do not run the full CI training matrix or long benchmark-scale fits by default.
- Do not require the original checkout for runtime instructions.
- Do not treat a successful import as proof that the model/config contract is valid.
