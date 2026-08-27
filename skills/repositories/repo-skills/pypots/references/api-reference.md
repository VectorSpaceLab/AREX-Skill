# API Reference

Read this file when you need verified package contracts: base classes, helper
methods, return keys, and the shape of the public model constructors.

## Top-Level Package Shape

The installed package exposes lazy-loaded task modules under `pypots`:

- `pypots.imputation`
- `pypots.forecasting`
- `pypots.classification`
- `pypots.anomaly_detection`
- `pypots.clustering`
- `pypots.representation`
- `pypots.data`
- `pypots.optim`
- `pypots.utils`

The CLI entry point is `pypots-cli` and resolves to `pypots.cli.pypots_cli:main`.

## Shared Model Contracts

### `BaseModel`

Owns device selection, checkpoint path setup, save/load, and the abstract
`fit()` / `predict()` contract.

Key points:

- `device` accepts a string, `torch.device`, list of devices, or `None`.
- Default device selection prefers CUDA when available, then CPU.
- `saving_path` controls checkpoint and TensorBoard output.
- `model_saving_strategy` accepts `None`, `"best"`, `"better"`, or `"all"`.
- `load()` uses a safe `torch.load(..., weights_only=False)` path when the local
  PyTorch version supports that argument.

### `BaseNNModel`

Owns training-loop state for neural models.

Common attributes:

- `best_loss`
- `best_epoch`
- `best_model_dict`
- `summary_writer`
- `optimizer` or task-specific optimizer fields on concrete models

### Task Base Classes

| Base class | Public helper | Result key | Typical input keys |
| --- | --- | --- | --- |
| `BaseImputer` / `BaseNNImputer` | `impute()` | `imputation` | `X`, optionally `X_ori` |
| `BaseForecaster` / `BaseNNForecaster` | `forecast()` | `forecasting` | `X`, `X_pred` |
| `BaseClassifier` / `BaseNNClassifier` | `predict_proba()`, `classify()` | `classification_proba`, `classification` | `X`, `y` |
| `BaseDetector` / `BaseNNDetector` | `detect()` | `anomaly_detection` | `X`, optionally anomaly labels |
| `BaseClusterer` / `BaseNNClusterer` | `cluster()` | `clustering` | `X`, `y` for validation only |
| `BaseRepresentor` / `BaseNNRepresentor` | `represent()` | `representation` | `X`, `y` for validation only |

### Common Predict/Train Forms

Most task wrappers follow this pattern:

- `fit(train_set, val_set=None, file_type="hdf5")`
- `predict(test_set, file_type="hdf5", **kwargs)`

Inputs can be in-memory dicts or HDF5 file paths.

## Common Constructor Knobs

Across the neural models, the recurring training knobs are:

- `batch_size`
- `epochs`
- `patience`
- `training_loss`
- `validation_metric`
- `optimizer`
- `num_workers`
- `device`
- `saving_path`
- `model_saving_strategy`
- `verbose`

Use the task-specific subskill when a model needs extra fields such as
`n_pred_steps`, `n_classes`, `anomaly_rate`, `n_clusters`, `G_optimizer`, or
`D_optimizer`.

## Representative Verified Signatures

The installed package matches the following patterns:

| Model | Signature focus | Notes |
| --- | --- | --- |
| `Mean`, `Median`, `Lerp` | no constructor args | rule-based / no training |
| `LOCF` | `first_step_imputation='zero'`, `device=None` | rule-based / no training |
| `SAITS` | `n_steps`, `n_features`, `n_layers`, `d_model`, `n_heads`, `d_k`, `d_v`, `d_ffn` | classic imputation model with standard NN training knobs |
| `USGAN` | `n_steps`, `n_features`, `rnn_hidden_size`, `G_optimizer`, `D_optimizer` | GAN-style dual optimizer |
| `TEFN` (imputation) | `n_fod`, `apply_nonstationary_norm`, `ORT_weight`, `MIT_weight` | specialized imputation architecture |
| `BTTF` | `n_steps`, `n_features`, `pred_step`, `rank`, `time_lags`, `burn_iter`, `gibbs_iter` | classical forecasting model |
| `TEFN` (forecasting) | `n_pred_steps`, `n_pred_features`, `n_fod`, `apply_nonstationary_norm` | forecasting variant, not the same class surface as imputation |
| `TimeMixer` | `term`, `n_layers`, `d_model`, `d_ffn`, `top_k`, `downsampling_layers`, `downsampling_window` | forecasting backbone with extra decomposition knobs |
| `Raindrop` | `n_steps`, `n_features`, `n_classes`, `n_layers`, `d_model`, `n_heads`, `d_ffn`, `aggregation`, `sensor_wise_mask`, `static` | optional GNN backend in the backbone |
| `TS2Vec` | `n_steps`, `n_features`, `n_classes`, `n_output_dims`, `d_hidden`, `n_layers` | used in both classification and representation workflows |
| `TimesNet` | task-specific variants for classification/anomaly/imputation/forecasting | backbone-adapted family with task-specific wrappers |
| `CRLI` | `n_clusters`, `n_generator_layers`, `rnn_hidden_size`, `rnn_cell_type`, `G_optimizer`, `D_optimizer` | clustering with latent variables |
| `VaDER` | `n_clusters`, `rnn_hidden_size`, `d_mu_stddev`, `pretrain_epochs` | clustering with pretraining |

## Result Handling Notes

- `predict()` always returns a dictionary.
- The task helper methods pull a specific key out of that dictionary and return
  just the array-like payload.
- When a task supports latent variables, pass `return_latent_vars=True` to the
  task-specific `predict()` method and then read the nested `latent_vars`
  mapping.

## Evaluation Helpers

The verified functional helpers exposed through `pypots.nn.functional` include:

- `calc_mse`, `calc_mae`, `calc_rmse`, `calc_mre`
- `calc_acc`, `calc_precision_recall_f1`, `calc_binary_classification_metrics`
- `calc_external_cluster_validation_metrics`, `calc_internal_cluster_validation_metrics`
- `gather_listed_dicts`
- `autocast`

Use these helpers in references and smoke checks instead of reimplementing metric
math in the skill files.
