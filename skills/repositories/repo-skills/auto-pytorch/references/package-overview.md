# Package overview

This file summarizes the public surface that the skill routes most often.

## Distribution and install

- Distribution name: `autoPyTorch`
- Public install command: `pip install autoPyTorch`
- Forecasting extra: `pip install autoPyTorch[forecasting]`

## Core public tasks

- `autoPyTorch.api.tabular_classification.TabularClassificationTask`
- `autoPyTorch.api.tabular_regression.TabularRegressionTask`
- `autoPyTorch.api.time_series_forecasting.TimeSeriesForecastingTask`

## Core helpers

- `autoPyTorch.api.base_task.BaseTask`
- `autoPyTorch.utils.pipeline.get_dataset_requirements`
- `autoPyTorch.utils.pipeline.get_configuration_space`
- `autoPyTorch.data.tabular_validator.TabularInputValidator`
- `autoPyTorch.data.time_series_forecasting_validator.TimeSeriesForecastingInputValidator`
- `autoPyTorch.utils.results_visualizer.PlotSettingParams`
- `autoPyTorch.utils.results_visualizer.ColorLabelSettings`

## Common task methods

- `search(...)`
- `fit_pipeline(...)`
- `refit(...)`
- `predict(...)`
- `score(...)`
- `show_models()`
- `sprint_statistics()`
- `plot_perf_over_time(...)`

## Supported problem families

- Tabular classification
- Tabular regression
- Time series forecasting

## Not a primary route

- Image classification is present in the source tree but is treated as a proof-of-concept path rather than a core workflow in this skill.
