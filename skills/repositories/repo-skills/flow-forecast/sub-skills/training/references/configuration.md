# Training Configuration

## Top-Level Shape

Most Flow Forecast training jobs use a JSON object with these blocks:

```json
{
  "model_name": "LSTM",
  "model_type": "PyTorch",
  "model_params": {},
  "dataset_params": {},
  "training_params": {},
  "inference_params": {},
  "metrics": ["MSE"],
  "wandb": false,
  "GCS": false
}
```

## Required Blocks

### `model_name`

A key from `flood_forecast.model_dict_function.pytorch_model_dict` when `model_type` is `"PyTorch"`.

### `model_type`

- `"PyTorch"` for the main model zoo path.
- `"da_rnn"` for the DA-RNN helper path.

### `model_params`

Constructor arguments for the selected model. The exact keys vary by model family; see [model-configs.md](model-configs.md).

### `dataset_params`

Loader and split parameters.

Common fields:

- `class`: loader family string such as `default`, `AutoEncoder`, `TemporalLoader`, `SeriesIDLoader`, `GeneralClassificationLoader`, or `VariableSequenceLength`.
- `training_path`, `validation_path`, `test_path`: local path, GCS URI, or other path accepted by `get_data()`.
- `forecast_history`, `forecast_length`: primary history and forecast window sizes.
- `target_col`, `relevant_cols`: target and feature columns.
- `scaler` or `scaling`: scaler name or scaler object source for the training path.
- `interpolate`: interpolation helper and arguments.
- `sort_column`: datetime or ordering column.
- `feature_param`: datetime-feature generation settings.
- `series_id_col` / `id_series_col`: multi-series identifier column.
- `temporal_feats`: temporal feature columns for `TemporalLoader`.
- `sequence_length`: classification/window length for `GeneralClassificationLoader`.
- `series_marker_column` and `task`: variable-length loader settings.

### `training_params`

The trainer expects at least:

- `criterion`: loss name or list of loss names.
- `optimizer`: optimizer name.
- `optim_params`: keyword arguments for the optimizer.
- `lr`: learning rate.
- `epochs`: number of training epochs.
- `batch_size`: training batch size.

Optional but common:

- `criterion_params`: constructor kwargs for a loss.
- `shuffle`: whether the training loader should shuffle.
- `pin_memory`, `num_workers`: data-loader tuning.

### `inference_params`

The trainer uses this block for post-fit evaluation of forecasting models.

Common fields:

- `datetime_start`: forecast start timestamp.
- `hours_to_forecast`: horizon for the held-out or inference window.
- `test_csv_path`: path to the evaluation CSV.
- `dataset_params`: loader settings for test-time slicing.
- `decoder_params`: decoder helper settings such as `simple_decode`.
- `num_prediction_samples`: optional CI sampling count.

## Important Optional Fields

- `weight_path`: load pretrained weights before fitting or inference.
- `weight_path_add`: transfer-learning helpers such as `excluded_layers` or `frozen_layers`.
- `early_stopping`: patience configuration for `EarlyStopper`.
- `meta_data`: path to a secondary config when the model uses meta-data fusion.
- `forward_params`: extra keyword arguments that should be passed into the model's forward call.
- `takes_target`: set for models that consume the target tensor during training.
- `use_decoder`: enable decoder-style validation logic in `train_transformer_style`.

## Minimal Example

```json
{
  "model_name": "NARX",
  "model_type": "PyTorch",
  "model_params": {
    "n_time_series": 4,
    "forecast_history": 48,
    "output_seq_len": 24,
    "n_targets": 1,
    "n_target_lags": 48,
    "n_exog_lags": 48
  },
  "dataset_params": {
    "class": "default",
    "training_path": "train.csv",
    "validation_path": "valid.csv",
    "test_path": "test.csv",
    "forecast_history": 48,
    "forecast_length": 24,
    "target_col": ["cfs"],
    "relevant_cols": ["cfs", "precip", "temp", "dwpf"],
    "scaler": "StandardScaler"
  },
  "training_params": {
    "criterion": "MSE",
    "optimizer": "Adam",
    "optim_params": {},
    "lr": 0.001,
    "epochs": 5,
    "batch_size": 64
  },
  "inference_params": {
    "datetime_start": "2020-05-31",
    "hours_to_forecast": 336,
    "test_csv_path": "test.csv",
    "decoder_params": {"decoder_function": "simple_decode", "unsqueeze_dim": 1},
    "dataset_params": {
      "file_path": "test.csv",
      "forecast_history": 48,
      "forecast_length": 24,
      "relevant_cols": ["cfs", "precip", "temp", "dwpf"],
      "target_col": ["cfs"],
      "scaling": "StandardScaler",
      "interpolate_param": false
    }
  },
  "metrics": ["MSE"],
  "wandb": false,
  "GCS": false
}
```

## Validation Hint

If a config looks valid but training still fails immediately, check `references/troubleshooting.md` for registry mismatches, WandB shape errors, missing inference blocks, and loader-class-specific fields.
