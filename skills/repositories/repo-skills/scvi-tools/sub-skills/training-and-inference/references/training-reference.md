# Training Reference

This reference covers scvi-tools training execution and `Trainer` configuration. It assumes the model has already been selected and the data object or datamodule registry has already been set up.

## Main `train()` Shape

Most standard scvi-tools models inherit the unsupervised training mixin with this practical signature:

```python
model.train(
    max_epochs=None,
    accelerator="auto",
    devices="auto",
    train_size=None,
    validation_size=None,
    shuffle_set_split=True,
    load_sparse_tensor=False,
    batch_size=128,
    early_stopping=False,
    datasplitter_kwargs=None,
    plan_config=None,
    plan_kwargs=None,
    datamodule=None,
    trainer_config=None,
    **trainer_kwargs,
)
```

Important behavior:

- If `max_epochs=None`, scvi-tools uses a heuristic based on `n_obs`; with a custom datamodule lacking `n_obs`, pass `max_epochs` explicitly.
- `train_size`, `validation_size`, `shuffle_set_split`, `load_sparse_tensor`, and `batch_size` configure the default `scvi.dataloaders.DataSplitter`; they are not used the same way when a custom `datamodule` is supplied.
- `plan_config` is merged with `plan_kwargs`; explicit `plan_kwargs` values take precedence.
- `trainer_config` is merged with `**trainer_kwargs`; explicit trainer kwargs take precedence.
- After successful training, the model records `train_indices`, `validation_indices`, `test_indices`, `trainer`, `history_`, and `is_trained_` where applicable.

Some model families override the signature with model-specific options, but they still pass `accelerator`, `devices`, plan settings, and trainer settings into the same runner/Trainer path.

## Configuration Objects

Use structured configs when you want reusable, inspectable settings.

```python
from scvi.train import TrainerConfig, TrainingPlanConfig

plan_config = TrainingPlanConfig(lr=1e-3, weight_decay=0.0, compile=False)
trainer_config = TrainerConfig(
    accelerator="auto",
    devices="auto",
    early_stopping=True,
    early_stopping_monitor="elbo_validation",
    early_stopping_patience=10,
    check_val_every_n_epoch=1,
)

model.train(
    max_epochs=100,
    plan_config=plan_config,
    trainer_config=trainer_config,
)
```

Choose the config class that matches the training plan:

- `TrainingPlanConfig`: most unsupervised models such as `SCVI`.
- `SemiSupervisedTrainingPlanConfig`: semi-supervised training such as `SCANVI`.
- `AdversarialTrainingPlanConfig` or `SemiSupervisedAdversarialTrainingPlanConfig`: adversarial training plans.
- `PyroTrainingPlanConfig` or `LowLevelPyroTrainingPlanConfig`: Pyro-based models.
- `ClassifierTrainingPlanConfig`: classifier plans.

If unsure, use `plan_kwargs={...}` with documented training-plan parameters.

## Accelerator and Devices

Portable defaults:

```python
model.train(max_epochs=20, accelerator="auto", devices="auto")
```

CPU-only explicit run:

```python
model.train(max_epochs=20, accelerator="cpu", devices=1)
```

Single GPU run:

```python
model.train(max_epochs=100, accelerator="gpu", devices=1)
```

Multi-GPU DDP from a script:

```python
model.train(
    max_epochs=100,
    accelerator="gpu",
    devices=-1,
    strategy="ddp_find_unused_parameters_true",
    early_stopping=False,
)
```

Multi-GPU DDP from a notebook:

```python
model.train(
    max_epochs=100,
    accelerator="gpu",
    devices=-1,
    strategy="ddp_notebook_find_unused_parameters_true",
    early_stopping=False,
)
```

DDP caveats:

- Multi-GPU support is CUDA/NVIDIA oriented and not a substitute for installing GPU-enabled dependencies.
- scvi-tools disables early stopping automatically when the strategy uses a distributed sampler.
- Validation behavior and notebook process management can differ from single-device runs; prefer script execution for reproducible DDP jobs.
- Some model families default to early stopping; explicitly set `early_stopping=False` for DDP if a warning or validation failure appears.

## Validation Splits

Default behavior uses `DataSplitter`:

- `train_size=None` acts like `0.9` training and the remainder validation, with safeguards for tiny last batches.
- `validation_size=None` uses `1 - train_size`; if `train_size + validation_size < 1`, the leftover cells become test cells.
- `shuffle_set_split=True` shuffles split indices; use `False` for deterministic sequential splits.
- For exact splits, pass `datasplitter_kwargs={"external_indexing": [train_idx, val_idx, test_idx]}` where each element is a NumPy array. Empty validation/test arrays are allowed, but duplicate, overlapping, or missing indices are rejected or warned.

Example:

```python
model.train(
    max_epochs=50,
    train_size=0.85,
    validation_size=0.1,
    batch_size=256,
    shuffle_set_split=True,
)
```

Early stopping needs the monitored split to exist. For example, monitoring `elbo_validation` with no validation cells raises an error.

## Callbacks and Checkpointing

scvi-tools wraps Lightning callbacks with scvi-friendly defaults.

Early stopping:

```python
model.train(
    max_epochs=200,
    early_stopping=True,
    early_stopping_monitor="elbo_validation",
    early_stopping_patience=10,
    early_stopping_min_delta=0.0,
    early_stopping_mode="min",
    check_val_every_n_epoch=1,
)
```

Checkpointing with the built-in scvi-tools checkpoint callback:

```python
model.train(
    max_epochs=100,
    enable_checkpointing=True,
    checkpointing_monitor="elbo_validation",
)
```

Manual callback list:

```python
from scvi.train import SaveCheckpoint

model.train(
    max_epochs=100,
    callbacks=[SaveCheckpoint(monitor="elbo_validation", load_best_on_end=True)],
)
```

Common trainer kwargs include `logger`, `log_every_n_steps`, `log_save_dir`, `enable_progress_bar`, `progress_bar_refresh_rate`, `enable_model_summary`, `num_sanity_val_steps`, `strategy`, and any supported Lightning `Trainer` keyword.

## Inference Execution Patterns

After training, inference methods usually run on the model's registered AnnData unless a `dataloader` is supplied.

```python
latent = model.get_latent_representation(batch_size=512)
elbo = model.get_elbo()
```

For custom datamodules or alternate cell subsets, use a matching inference dataloader:

```python
inference_dl = datamodule.inference_dataloader(batch_size=512)
latent = model.get_latent_representation(dataloader=inference_dl)
elbo = model.get_elbo(dataloader=inference_dl)
```

Do not mix a dataloader from a different registry, feature order, batch encoding, or label encoding than the model expects.
