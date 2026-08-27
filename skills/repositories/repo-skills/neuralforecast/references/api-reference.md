# API Reference

## Purpose

Read this when you need verified object signatures, constructor arguments, or a
minimal reminder of the public NeuralForecast API surface.

## When to read

- Before writing a new core workflow.
- When a model constructor or Auto* wrapper raises a validation error.
- When you need to confirm which helper owns a column, backend, or loss option.

## Verified public entry points

| Object | Verified signature | Notes |
| --- | --- | --- |
| `neuralforecast.NeuralForecast` | `NeuralForecast(models, freq, local_scaler_type=None, local_static_scaler_type=None)` | Main forecasting wrapper. |
| `neuralforecast.utils.PredictionIntervals` | `PredictionIntervals(n_windows=2, method='conformal_distribution', step_size=1)` | Used by `fit(..., prediction_intervals=...)` and `predict(level=...)`. |
| `neuralforecast.tsdataset.TimeSeriesDataset.from_df` | `from_df(df, static_df=None, id_col='unique_id', time_col='ds', target_col='y')` | Panel conversion helper for long-format data. |
| `neuralforecast.tsdataset.TimeSeriesDataModule` | `TimeSeriesDataModule(dataset, batch_size=32, valid_batch_size=1024, drop_last=False, shuffle_train=True, **dataloaders_kwargs)` | Batches a prepared dataset. |
| `neuralforecast.common._base_auto.BaseAuto` | `BaseAuto(cls_model, h, loss, valid_loss, config, search_alg=..., num_samples=10, time_budget=None, refit_with_val=False, verbose=False, alias=None, backend='ray', callbacks=None, ray_options=None, optuna_options=None, cpus=None, gpus=None)` | Shared Auto* hyperparameter-search wrapper. |
| `neuralforecast.auto.AutoNHITS` | `AutoNHITS(h, loss=MAE(), valid_loss=None, config=None, search_alg=..., num_samples=10, time_budget=None, refit_with_val=False, cpus=None, gpus=None, verbose=False, alias=None, backend='ray', callbacks=None, ray_options=None, optuna_options=None)` | Representative Auto* wrapper. |
| `neuralforecast.auto.AutoMLP` | same pattern as `AutoNHITS` | Lightweight Auto* baseline. |
| `neuralforecast.common._base_model.DistributedConfig` | `DistributedConfig(partitions_path, num_nodes, devices)` | Spark distributed partitioning config. |
| `neuralforecast.common._base_auto.RayOptions` | `RayOptions(run_config=None, scheduler=None, cpus=None, gpus=None)` | Ray resource and scheduler wrapper. |
| `neuralforecast.common._base_auto.OptunaOptions` | `OptunaOptions(study_kwargs=None, create_study_kwargs=None)` | Optuna backend wrapper. |
| `neuralforecast.losses.pytorch.MAE` | `MAE(horizon_weight=None)` | Point loss used in the quickstart and tiny smoke. |
| `neuralforecast.losses.pytorch.MQLoss` | `MQLoss(level=[80, 90], quantiles=None, horizon_weight=None)` | Multi-quantile loss with level/quantile conversion. |
| `neuralforecast.losses.pytorch.DistributionLoss` | `DistributionLoss(distribution, level=[80, 90], quantiles=None, num_samples=1000, return_params=False, horizon_weight=None, **distribution_kwargs)` | Distribution family wrapper. |
| `neuralforecast.losses.pytorch.GMM` | `GMM(n_components=1, level=[80, 90], quantiles=None, num_samples=1000, return_params=False, batch_correlation=False, horizon_correlation=False, weighted=False)` | Gaussian mixture mesh loss. |
| `neuralforecast.losses.pytorch.sCRPS` | `sCRPS(level=[80, 90], quantiles=None)` | Scaled CRPS helper. |
| `neuralforecast.utils.generate_series` | `generate_series(n_series, freq='D', min_length=50, max_length=500, n_temporal_features=0, n_static_features=0, equal_ends=False, seed=0)` | Safe fixture generator used by tests and scripts. |

## Constructor and runtime facts worth remembering

- `NeuralForecast.fit` accepts pandas, Polars, Spark DataFrames, or a sequence of
  parquet file paths, plus optional `static_df` and `distributed_config`.
- `NeuralForecast.predict` and `cross_validation` can reuse the stored dataset
  when `df=None` after a successful fit.
- `NeuralForecast.save` and `NeuralForecast.load` provide portability for fitted
  models and their stored dataset.
- `TimeLLM` and `xLSTM` import successfully only as optional modules in this
  base inspection prefix; their feature flags are disabled without their extra
  dependencies.
- `neuralforecast.__version__` comes from installed distribution metadata, not
  from the checkout.

## Read next

- `data-formats.md` for panel schema, exogenous columns, and dataset conversion.
- `model-overview.md` for model-family selection and special capability flags.
- `losses-reference.md` for quantiles, distribution losses, and robust losses.
- `workflows.md` for quickstart, prediction intervals, simulation, and save/load.
- `tuning-distributed.md` for Auto*, Ray, Optuna, and Spark details.
