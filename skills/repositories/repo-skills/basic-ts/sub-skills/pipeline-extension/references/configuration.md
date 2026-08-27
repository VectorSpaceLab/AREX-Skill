# Configuration and Packing

## Purpose

Read this reference when you want to understand how BasicTS config objects are built, how shortcut fields are packed into task components, or how checkpoint/save settings are derived.

## Verified config classes

- `BasicTSConfig`
- `BasicTSForecastingConfig`
- `BasicTSClassificationConfig`
- `BasicTSImputationConfig`
- `BasicTSFoundationModelConfig`
- `BasicTSModelConfig`

`BasicTSModelConfig` is an `EasyDict`-style container used by model constructors.

## What the config classes do

The config classes:

- collect task defaults
- provide shortcut fields that the runner and builder consume
- serialize themselves to JSON under the checkpoint directory
- compute an MD5 key for the training-dependent part of the configuration

## Important shortcut fields

| Field | Meaning |
| --- | --- |
| `batch_size` | Sets train/val/test batch sizes together. |
| `input_len` | Forecasting/imputation input window shortcut. |
| `output_len` | Forecasting output horizon shortcut. |
| `use_timestamps` | Enables or disables timestamp loading. |
| `mask_ratio` | Imputation masking ratio. |
| `lr` | Shortcut for optimizer learning rate. |

If `batch_size` is set, it overrides the task-specific loader batch sizes.

## Task-specific defaults

### Forecasting

- Default dataset type: `BasicTSForecastingDataset`
- Default scaler: `ZScoreScaler`
- Default loss: `MAE`
- Default metrics: `MAE`, `MSE`, `RMSE`, `MAPE`, `WAPE`

### Classification

- Default dataset type: `UEADataset`
- Default loss: `CrossEntropyLoss`
- Default metrics: `Accuracy`
- Scaler is optional and defaults to `None`

### Imputation

- Default dataset type: `BasicTSImputationDataset`
- Default scaler: `ZScoreScaler`
- Default loss: `MAE`
- Uses `mask_ratio` to drive reconstruction masking

### Foundation model

- Default optimizer: `AdamW`
- Default scheduler: `CosineWarmup`
- Default training unit: step-based defaults
- Often uses `model_dtype` for mixed-precision style workflows

## Checkpoint settings

### `ckpt_save_dir`

If you do not set it, the forecasting/classification/imputation configs build a default path that includes:

- the model name
- the dataset name
- the training length settings

### `ckpt_save_strategy`

- `None`: remove the previous checkpoint each epoch
- `int`: save every N epochs
- `list` or `tuple`: save at chosen epochs

### `eval_after_train`

If `True`, the runner evaluates the best validation checkpoint after training.

### `save_results`

If `True`, the evaluation path saves results into the checkpoint directory.

## How packing works

The builder and config classes pack shortcut fields into the target component when that component's constructor accepts them.

Examples:

- dataset constructor receives `input_len`, `output_len`, `use_timestamps`, `memmap`, and related fields
- model config receives any matching shortcut fields
- optimizer and scheduler params are packed from the config into their constructors

## Serialization and refresh behavior

- `cfg.save()` writes the JSON config under the checkpoint directory.
- `cfg.md5` hashes the training-dependent parts of the config.
- If you change fields that affect the hash, the checkpoint path changes too.

## Runner-adjacent settings that matter

- `val_interval` and `test_interval` control when validation and test passes happen.
- `train_data_prefetch`, `val_data_prefetch`, and `test_data_prefetch` enable data-prefetch loader variants.
- `ddp_find_unused_parameters` matters when a model has conditionally unused parameters.
- `compile_model` enables `torch.compile` when the installed torch version supports it.

## Evidence sources

- `src/basicts/configs/base_config.py`
- `src/basicts/configs/tsf_config.py`
- `src/basicts/configs/tsc_config.py`
- `src/basicts/configs/tsi_config.py`
- `src/basicts/configs/tsfm_config.py`
- installed-package inspection in the CPU environment
- `docs/config_design.md`
