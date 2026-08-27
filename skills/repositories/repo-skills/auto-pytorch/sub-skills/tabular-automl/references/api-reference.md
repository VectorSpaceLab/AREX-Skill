# Tabular API reference

## Task classes

| Class | Purpose | Key notes |
| --- | --- | --- |
| `TabularClassificationTask` | End-to-end AutoML for classification | Default resampling is holdout validation; `enable_traditional_pipeline=True` by default |
| `TabularRegressionTask` | End-to-end AutoML for regression | Same control surface as classification, with regression metrics such as `r2` |
| `TabularClassificationPipeline` | Direct access to the tabular classification pipeline | Use when you already have dataset properties or a configuration |
| `TabularRegressionPipeline` | Direct access to the tabular regression pipeline | Same as classification, with regression-specific target handling |
| `TraditionalTabularClassificationPipeline` | Traditional-ML-only tabular classification pipeline | Useful for a fast baseline or explicit learner selection |
| `TraditionalTabularRegressionPipeline` | Traditional-ML-only tabular regression pipeline | Useful for a fast baseline or explicit learner selection |

## Constructor and search control highlights

### `TabularClassificationTask`

Important constructor arguments:

- `seed=1`
- `n_jobs=1`
- `n_threads=1`
- `ensemble_size=50`
- `ensemble_nbest=50`
- `max_models_on_disc=50`
- `include_components=None`
- `exclude_components=None`
- `resampling_strategy=HoldoutValTypes.holdout_validation`
- `backend=None`
- `search_space_updates=None`

Important `search(...)` arguments:

- `optimize_metric`
- `X_train`, `y_train`, `X_test`, `y_test`
- `dataset_name`
- `feat_types`
- `budget_type='epochs'`
- `min_budget=5`, `max_budget=50`
- `total_walltime_limit=100`
- `func_eval_time_limit_secs=None`
- `enable_traditional_pipeline=True`
- `memory_limit=4096`
- `all_supported_metrics=True`
- `precision=32`
- `disable_file_output=None`
- `load_models=True`
- `portfolio_selection=None`
- `dataset_compression=False`

### `TabularRegressionTask`

Same control surface as the classification task, but with regression-oriented defaults and score names.

## Single-config fitting

`fit_pipeline(...)` is the low-level API for a single configuration.

Important arguments:

- `configuration`
- `dataset` or raw `X_train` / `y_train` / `X_test` / `y_test`
- `resampling_strategy` and `resampling_strategy_args`
- `run_time_limit_secs=60`
- `memory_limit=None`
- `eval_metric=None`
- `budget_type=None`
- `include_components`, `exclude_components`
- `search_space_updates`
- `budget=None`
- `pipeline_options=None`
- `disable_file_output=None`

Returns:

- fitted pipeline or `None`
- `RunInfo`
- `RunValue`
- `BaseDataset`

## Validation classes

| Class | Purpose | Important notes |
| --- | --- | --- |
| `TabularInputValidator` | Validates and encodes tabular features and targets | Accepts lists, NumPy arrays, pandas DataFrames, and some sparse inputs |
| `TabularFeatureValidator` | Encodes categorical features and records column types | Use `feat_types` when NumPy dtypes hide categories |
| `TabularTargetValidator` | Encodes classification labels and normalizes regression targets | Raises clear errors for unsupported target shapes or types |

## Metrics and inspection helpers

- `show_models()` returns a markdown table of ensemble members and weights.
- `sprint_statistics()` returns a text summary of the AutoML run.
- `plot_perf_over_time(...)` uses `PlotSettingParams` and `ColorLabelSettings`.

## Traditional learner notes

`ModelChoice` resolves the available traditional learners. The built-in roster includes:

- `lgb`
- `catboost`
- `random_forest`
- `extra_trees`
- `svm`
- `knn`

`TabularTraditionalModel` wraps those learners and filters some choices based on dataset properties.

## Public utility hooks

- `get_dataset_requirements(info, include=None, exclude=None, search_space_updates=None)`
- `get_configuration_space(info, include=None, exclude=None, search_space_updates=None)`

These utilities are helpful when you want to reason about the dataset properties required by a pipeline before you fit it.
