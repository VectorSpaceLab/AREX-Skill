# Forecasting API reference

## Task class

| Class | Purpose | Key notes |
| --- | --- | --- |
| `TimeSeriesForecastingTask` | End-to-end AutoML for time series forecasting | `enable_traditional_pipeline=False` by default |

## Constructor and search control highlights

### `TimeSeriesForecastingTask`

Important constructor arguments:

- `seed=1`
- `n_jobs=1`
- `ensemble_size=50`
- `ensemble_nbest=50`
- `max_models_on_disc=50`
- `include_components=None`
- `exclude_components=None`
- `resampling_strategy=HoldoutValTypes.time_series_hold_out_validation`
- `backend=None`
- `search_space_updates=None`

Important `search(...)` arguments:

- `optimize_metric`
- `X_train`, `y_train`, `X_test`, `y_test`
- `n_prediction_steps=1`
- `freq=None`
- `start_times=None`
- `series_idx=None`
- `dataset_name=None`
- `budget_type='epochs'`
- `min_budget=5`, `max_budget=50`
- `total_walltime_limit=100`
- `func_eval_time_limit_secs=None`
- `enable_traditional_pipeline=False`
- `memory_limit=4096`
- `all_supported_metrics=True`
- `precision=32`
- `disable_file_output=[]`
- `load_models=True`
- `portfolio_selection=None`
- `suggested_init_models=None`
- `custom_init_setting_path=None`
- `min_num_test_instances=None`
- `dataset_compression=False`
- forecasting-specific `**kwargs`

## Prediction surface

`predict(...)` can take either:

- `List[TimeSeriesSequence]`
- raw future features plus `past_targets`

The task returns forecast outputs shaped as:

- `(B, H)` for one target
- `(B, H, N)` for multiple targets

where `B` is the number of series, `H` is the horizon, and `N` is the number of targets.

## Validation classes

| Class | Purpose | Important notes |
| --- | --- | --- |
| `TimeSeriesForecastingInputValidator` | Validates and transforms forecasting inputs | Handles uni-variant and multi-variant layouts |
| `TimeSeriesFeatureValidator` | Reorders and encodes feature columns | Tracks static features and series identifiers |
| `TimeSeriesTargetValidator` | Validates and encodes forecasting targets | Missing values are allowed; classification is not supported |

## Dataset helpers

- `TimeSeriesForecastingDataset` stores the transformed series and generates test sequences.
- `TimeSeriesSequence` provides the indexed series windows used by the model.
- `compute_freq_values(...)` and the loader/window helpers determine usable window sizes.

## Metric names that matter most

- `mean_MASE_forecasting`
- `median_MASE_forecasting`
- `mean_MAE_forecasting`
- `median_MAE_forecasting`
- `mean_MAPE_forecasting`
- `median_MAPE_forecasting`
- `mean_MSE_forecasting`
- `median_MSE_forecasting`

## Public utility hooks

- `get_dataset_requirements(info, include=None, exclude=None, search_space_updates=None)`
- `get_configuration_space(info, include=None, exclude=None, search_space_updates=None)`

These are helpful when you want to understand what dataset properties the forecasting pipeline expects before you fit it.
