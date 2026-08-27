# Estimator API reference

This reference is distilled from the installed package inspection for auto-sklearn 0.16.0dev/0.16.0.dev0, the public API docs, estimator source, AutoML source, ASKL2 source, and estimator tests. The Python package imports as `autosklearn`.

## Imports and class selection

| Need | Import | Class | Notes |
|---|---|---|---|
| Binary or multiclass classification | `import autosklearn.classification` | `autosklearn.classification.AutoSklearnClassifier` | Standard classifier. Supports `predict` and `predict_proba`. |
| Multilabel classification | `import autosklearn.classification` | `autosklearn.classification.AutoSklearnClassifier` | Target must be multilabel indicator-style, usually a 2-D array of `0/1` labels. |
| Regression | `import autosklearn.regression` | `autosklearn.regression.AutoSklearnRegressor` | Standard regressor. No `predict_proba`. |
| Multioutput regression | `import autosklearn.regression` | `autosklearn.regression.AutoSklearnRegressor` | Target is 2-D continuous output, predictions are shape `(n_samples, n_outputs)`. |
| Auto-sklearn 2.0 classification | `from autosklearn.experimental.askl2 import AutoSklearn2Classifier` | `AutoSklearn2Classifier` | Same estimator style as the standard classifier, but chooses ASKL2 strategies/portfolio defaults automatically. |

## Observed public signatures

```python
AutoSklearnEstimator(
    time_left_for_this_task=3600,
    per_run_time_limit=None,
    initial_configurations_via_metalearning=25,
    ensemble_size=None,
    ensemble_class="default",
    ensemble_kwargs=None,
    ensemble_nbest=50,
    max_models_on_disc=50,
    seed=1,
    memory_limit=3072,
    include=None,
    exclude=None,
    resampling_strategy="holdout",
    resampling_strategy_arguments=None,
    tmp_folder=None,
    delete_tmp_folder_after_terminate=True,
    n_jobs=None,
    dask_client=None,
    disable_evaluator_output=False,
    get_smac_object_callback=None,
    smac_scenario_args=None,
    logging_config=None,
    metadata_directory=None,
    metric=None,
    scoring_functions=None,
    load_models=True,
    get_trials_callback=None,
    dataset_compression=True,
    allow_string_features=True,
    disable_progress_bar=False,
)
```

```python
AutoSklearnClassifier.fit(X, y, X_test=None, y_test=None, feat_type=None, dataset_name=None)
AutoSklearnClassifier.predict(X, batch_size=None, n_jobs=1)
AutoSklearnClassifier.predict_proba(X, batch_size=None, n_jobs=1)

AutoSklearnRegressor.fit(X, y, X_test=None, y_test=None, feat_type=None, dataset_name=None)
AutoSklearnRegressor.predict(X, batch_size=None, n_jobs=1)

AutoSklearn2Classifier(
    time_left_for_this_task=3600,
    per_run_time_limit=None,
    ensemble_size=None,
    ensemble_class=EnsembleSelection,
    ensemble_kwargs=None,
    ensemble_nbest=50,
    max_models_on_disc=50,
    seed=1,
    memory_limit=3072,
    tmp_folder=None,
    delete_tmp_folder_after_terminate=True,
    n_jobs=None,
    dask_client=None,
    disable_evaluator_output=False,
    smac_scenario_args=None,
    logging_config=None,
    metric=None,
    scoring_functions=None,
    load_models=True,
    dataset_compression=True,
    allow_string_features=True,
    disable_progress_bar=False,
)
AutoSklearn2Classifier.fit(X, y, X_test=None, y_test=None, metric=None, feat_type=None, dataset_name=None)
```

`output_directory` is mentioned in older/public FAQ text as controlling saved test predictions, but it is not present in the observed estimator constructors for this 0.16.0dev package. Do not pass it unless the active installed signature is rechecked and includes it. For this generated skill, use `tmp_folder` and `delete_tmp_folder_after_terminate` for run output/log control.

## Constructor knobs by purpose

| Purpose | Parameters | Operating guidance |
|---|---|---|
| Fit budget | `time_left_for_this_task`, `per_run_time_limit`, `memory_limit` | Defaults are long. For interactive smoke, choose seconds/minutes and state that quality is not proven. Too-tight values commonly produce dummy-only runs or timeout/memory failures. |
| Reproducibility and outputs | `seed`, `tmp_folder`, `delete_tmp_folder_after_terminate`, `logging_config` | Use a unique `tmp_folder` when logs/models should be inspected. Keep `delete_tmp_folder_after_terminate=False` only when the user wants artifacts; otherwise allow cleanup. |
| Model loading/output | `load_models`, `disable_evaluator_output` | Keep `load_models=True` and `disable_evaluator_output=False` when later `predict`, `show_models`, or `fit_ensemble` is expected. `disable_evaluator_output=True` disables model/prediction output and cannot be used with normal ensemble prediction workflows. |
| Ensemble basics | `ensemble_class`, `ensemble_kwargs`, `ensemble_nbest`, `max_models_on_disc`, deprecated `ensemble_size` | Basic use can keep defaults. For deep ensemble choices, model retention trade-offs, and `performance_over_time_`, route to [search-and-parallelism](../../search-and-parallelism/). |
| Search-space filters | `include`, `exclude` | Standard classifier/regressor accept these filters. Route component IDs and custom components to [custom-components](../../custom-components/) and search strategy details to [search-and-parallelism](../../search-and-parallelism/). |
| Data, metrics, and validation | `metric`, `scoring_functions`, `resampling_strategy`, `resampling_strategy_arguments`, `dataset_compression`, `allow_string_features` | Mention only enough to pass through; route details to [data-metrics-validation](../../data-metrics-validation/). |
| Parallel/search internals | `n_jobs`, `dask_client`, `get_smac_object_callback`, `smac_scenario_args`, `get_trials_callback`, `disable_progress_bar` | Route setup and pitfalls to [search-and-parallelism](../../search-and-parallelism/). |
| Metadata | `initial_configurations_via_metalearning`, `metadata_directory` | Route metadata refresh and ASKL2 selector context to [metadata-maintenance](../../metadata-maintenance/). |

## Fit arguments

| Argument | Applies to | Meaning |
|---|---|---|
| `X`, `y` | all estimators | Training features and target. Supported feature/target formats are owned by [data-metrics-validation](../../data-metrics-validation/). |
| `X_test`, `y_test` | all estimators | Optional held-out data used to save/evaluate test predictions over time when output is enabled. Useful for later inspection. |
| `feat_type` | all estimators | Optional list describing features for non-DataFrame inputs. Details and valid labels route to [data-metrics-validation](../../data-metrics-validation/). |
| `dataset_name` | all estimators | Human-readable dataset label used in logs/statistics and meta-learning exclusion context for standard auto-sklearn. Use a short non-sensitive string. |
| `metric` on `AutoSklearn2Classifier.fit` | ASKL2 only | Optional fit-time metric override for ASKL2; if not supplied, ASKL2 chooses accuracy for 1-D targets and log loss for multi-label/multi-output-like classification targets. |

## Supported target types

| Estimator | Supported targets | Rejected/common mistakes |
|---|---|---|
| `AutoSklearnClassifier` | binary, multiclass, multilabel-indicator | continuous regression targets, multiclass-multioutput, continuous-multioutput. |
| `AutoSklearnRegressor` | continuous, binary numeric, multiclass numeric, continuous-multioutput | multilabel-indicator and multiclass-multioutput. |
| `AutoSklearn2Classifier` | classifier target types above | Same classifier target validation, with ASKL2 automatic strategy selection. Sparse `X` reduces its classifier set by excluding gradient boosting. |

Use `sklearn.utils.multiclass.type_of_target(y)` before fit when target shape or dtype is unclear. For target encoding, categorical columns, `feat_type`, and string behavior, use [data-metrics-validation](../../data-metrics-validation/).

## Post-fit methods and attributes

| Method/attribute | Return/shape | Use |
|---|---|---|
| `predict(X, batch_size=None, n_jobs=1)` | Class labels or regression values. Classification may return `(n_samples,)` or `(n_samples, n_labels)`; regression may return `(n_samples,)` or `(n_samples, n_outputs)`. | Main inference entry point. Prediction `n_jobs` is separate from training `n_jobs`; for parallel inference details route to [search-and-parallelism](../../search-and-parallelism/). |
| `predict_proba(X, batch_size=None, n_jobs=1)` | Classification probabilities. Non-multilabel rows should sum to 1; multilabel output has one probability per label and rows do not need to sum to 1. | Classifier only. Validate range `[0, 1]`. |
| `score(X, y)` | Numeric score using estimator/default scoring | Quick sanity check after fit/refit. Use explicit metrics for real evaluation. |
| `refit(X, y)` | `self` | Fits all selected models on supplied data. Necessary after cross-validation before predicting new data, and useful after holdout to train final models on all training data. |
| `fit_ensemble(y, task=None, precision=32, dataset_name=None, ensemble_kwargs=None, ensemble_nbest=None, ensemble_class="default", metric=None)` | `self` | Builds/rebuilds an ensemble from already saved optimization outputs. Requires model/prediction output to exist; do not combine with disabled evaluator output. |
| `leaderboard(detailed=False, ensemble_only=True, top_k="all", sort_by="cost", sort_order="auto", include=None)` | pandas `DataFrame` indexed by `model_id` | Basic model/ranking table. Use `ensemble_only=False` for all evaluated models. Use `detailed=True` or `include=[...]` for columns. |
| `show_models()` | `dict[int, dict]` | Final ensemble members keyed by model id. Holdout rows include preprocessors and `classifier`/`regressor` plus `sklearn_classifier`/`sklearn_regressor`; CV rows include a `voting_model` and an `estimators` list. |
| `sprint_statistics()` | multiline string | Run summary with dataset name, metric, best validation score, and counts of successful/crashed/timeout/memory-limit runs. First check for dummy-only or failed-run situations. |
| `cv_results_` | dict suitable for `pandas.DataFrame` | Compatibility-style run results. Basic use can inspect keys/lengths; deep interpretation routes to [search-and-parallelism](../../search-and-parallelism/). |
| `performance_over_time_` | pandas `DataFrame` | Performance trajectory. Route plotting and interpretation to [search-and-parallelism](../../search-and-parallelism/). |
| `get_models_with_weights()` | list of `(weight, pipeline)` pairs | Inspect final weighted pipelines when output was saved and models are loaded. Deep component inspection routes to [search-and-parallelism](../../search-and-parallelism/). |

## Leaderboard columns

Simple single-objective columns include `rank`, `ensemble_weight`, `type`, `cost`, and `duration` with `model_id` as index. Detailed columns add `config_id`, `train_loss`, `seed`, `start_time`, `end_time`, `budget`, `status`, `data_preprocessors`, `feature_preprocessors`, `balancing_strategy`, and `config_origin`.

For multi-objective optimization, `cost` is split into `cost_0`, `cost_1`, and so on. `top_k` must be a positive integer or `'all'`; `sort_order` must be `'auto'`, `'ascending'`, or `'descending'`; `include` cannot be just `'model_id'`.

## AutoSklearn2Classifier specifics

`AutoSklearn2Classifier` is experimental and classifier-only. It trains/loads selector files under the user's home cache or `XDG_CACHE_HOME`, then uses packaged training data and portfolios to choose an AutoML policy. It sets `include` internally to a smaller classifier set (`extra_trees`, `passive_aggressive`, `random_forest`, `sgd`, `gradient_boosting`, `mlp`; sparse data excludes `gradient_boosting`) and `feature_preprocessor` to `no_preprocessing`. It does not expose the standard classifier's explicit `include`, `exclude`, `resampling_strategy`, `resampling_strategy_arguments`, `metadata_directory`, `initial_configurations_via_metalearning`, `get_smac_object_callback`, or `get_trials_callback` constructor arguments.

If ASKL2 cannot create selector files because the home cache or `XDG_CACHE_HOME` is unwritable, choose a writable cache directory or fall back to `AutoSklearnClassifier` with explicit settings.
