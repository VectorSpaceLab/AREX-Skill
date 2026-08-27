# Tabular API Reference

This reference summarizes the public tabular APIs future agents should use most often. It is distilled from AutoGluon tabular predictor implementation, tabular config files, feature metadata/generator implementation, tutorial material, examples, tests, and installed-package inspection.

## Imports

```python
from autogluon.tabular import TabularDataset, TabularPredictor
from autogluon.common.features.feature_metadata import FeatureMetadata
```

`TabularDataset(data)` is a convenience wrapper that returns a `pandas.DataFrame`. It accepts local CSV/Parquet paths, `DataFrame`, numpy-like arrays, iterables, or dictionaries. For existing pandas data, passing the `DataFrame` directly to `TabularPredictor.fit` is equally valid.

## `TabularPredictor` Constructor

Installed signature:

```python
TabularPredictor(
    label,
    problem_type=None,
    eval_metric=None,
    path=None,
    verbosity=2,
    log_to_file=False,
    log_file_path="auto",
    sample_weight=None,
    weight_evaluation=False,
    groups=None,
    positive_class=None,
    **kwargs,
)
```

Key choices:

- `label`: target column name; it must exist in training data and in any evaluation data passed to `evaluate` or scored `leaderboard`.
- `problem_type`: optional explicit task type: `"binary"`, `"multiclass"`, `"regression"`, or `"quantile"`. If omitted, AutoGluon infers it from label values.
- `eval_metric`: metric name or AutoGluon scorer. Defaults are `accuracy` for classification, `root_mean_squared_error` for regression, and `pinball_loss` for quantile prediction.
- `path`: predictor artifact directory. If omitted, AutoGluon creates a timestamped `AutogluonModels/ag-*` directory in the current process working directory.
- `sample_weight`: either a column name, `"auto_weight"`, `"balance_weight"`, or `None`. A weight column is not used as a feature.
- `weight_evaluation`: if true, evaluation metrics use `sample_weight`; evaluation data must include the weight column.
- `groups`: experimental group column for Leave-One-Group-Out splitting during bagging; ignored if bagging is not enabled.
- `positive_class`: controls the positive class for binary metrics such as F1 when automatic class ordering is not desired.
- `learner_kwargs`: advanced inner learner settings such as `ignored_columns`, `label_count_threshold`, and `cache_data`.
- `quantile_levels`: advanced constructor kwarg for quantile prediction, usually paired with `problem_type="quantile"`.

Path caution: use a fresh empty `path` for independent fits. Reusing a predictor path can overwrite prior artifacts.

## `fit`

Installed signature:

```python
predictor.fit(
    train_data,
    tuning_data=None,
    time_limit=None,
    presets=None,
    hyperparameters=None,
    feature_metadata="infer",
    infer_limit=None,
    infer_limit_batch_size=None,
    fit_weighted_ensemble=True,
    fit_full_last_level_weighted_ensemble=True,
    full_weighted_ensemble_additionally=False,
    dynamic_stacking=False,
    calibrate_decision_threshold="auto",
    num_cpus="auto",
    num_gpus="auto",
    fit_strategy="sequential",
    memory_limit="auto",
    callbacks=None,
    **kwargs,
)
```

Important fit arguments:

- `train_data`: `DataFrame` or file path. Must include the label column.
- `tuning_data`: validation data used for early stopping, HPO, ensembling, and calibration. It is not an unbiased test set.
- `time_limit`: approximate wallclock budget in seconds for training.
- `presets`: named configuration(s) such as `"medium_quality"`, `"good_quality"`, `"high_quality"`, `"best_quality"`, `"extreme_quality"`, `"optimize_for_deployment"`, `"interpretable"`, or `"ignore_text"`. Lists apply in order; later presets override earlier presets for the same setting.
- `hyperparameters`: string preset or dictionary of model families to train. Common keys include `GBM`, `CAT`, `XGB`, `RF`, `XT`, `KNN`, `LR`, `NN_TORCH`, `FASTAI`, `REALMLP`, `TABM`, `MITRA`, `TABICL`, `TABPFNV2`, and `AG_AUTOMM`.
- `feature_metadata`: `"infer"` or a `FeatureMetadata` object to override raw/special feature types.
- `infer_limit`: maximum per-row inference latency target. If impossible, fit can raise.
- `num_cpus`, `num_gpus`: total resources available to AutoGluon; use `num_gpus=0` for CPU-only runs.
- `fit_strategy`: `"sequential"` is stable; `"parallel"` uses Ray and is experimental, CPU-focused, and more memory-sensitive.
- `memory_limit`: soft total memory budget in GB or `"auto"`.
- `calibrate_decision_threshold`: for binary classification, `"auto"` can calibrate prediction thresholds for class-based metrics.

Common advanced `fit` kwargs:

- `auto_stack=True`: automatically choose bagging and stack ensembling.
- `num_bag_folds`: k-fold bagging count; values 5-10 are common for accuracy, `0` disables bagging, `1` is invalid.
- `num_bag_sets`: repeated bagging count; use sparingly because it multiplies runtime.
- `num_stack_levels`: stack ensemble depth; requires bagging when greater than zero.
- `use_bag_holdout`: use `tuning_data` or a holdout for weighted ensemble optimization during bagging.
- `hyperparameter_tune_kwargs`: HPO configuration; use `"auto"`, `"random"`, or an explicit dictionary with `num_trials`, `scheduler`, and `searcher`.
- `included_model_types` / `excluded_model_types`: include or exclude model family keys without rewriting the full hyperparameter dictionary.
- `refit_full`: retrain selected models on all available train+tuning data after model selection.
- `set_best_to_refit_full`: make refit-full variants the default prediction model when available.
- `save_bag_folds=False`: reduces disk usage only when paired with `refit_full` / `set_best_to_refit_full` planning.
- `feature_prune_kwargs`: layer-wise feature pruning using permutation importance.
- `ag_args`, `ag_args_fit`, `ag_args_ensemble`: model-level and ensemble-level controls.

## Prediction And Evaluation

Installed signatures:

```python
predictor.predict(data, model=None, as_pandas=True, transform_features=True, decision_threshold=None)
predictor.predict_proba(data, model=None, as_pandas=True, as_multiclass=True, transform_features=True)
predictor.evaluate(data, model=None, decision_threshold=None, display=False, auxiliary_metrics=True, detailed_report=False)
predictor.evaluate_predictions(y_true, y_pred, sample_weight=None, decision_threshold=None, display=False, auxiliary_metrics=True, detailed_report=False)
```

Usage notes:

- `predict(data)` accepts a `DataFrame` or file path; label and extra columns are ignored for prediction.
- `predict_proba` is valid for classification only. Check `predictor.can_predict_proba` before calling if the problem type may be regression or quantile.
- Binary `predict_proba(as_multiclass=True)` returns columns in `predictor.class_labels` order. `as_multiclass=False` returns only positive-class probabilities.
- `evaluate(data)` requires the label column. If weighted evaluation is enabled, the sample-weight column must also be present.
- Metric scores are returned in higher-is-better form. Error metrics such as RMSE and log loss appear with signs flipped in leaderboard/evaluation outputs.
- For binary metrics sensitive to thresholds, calibrate or pass `decision_threshold` instead of assuming `0.5`.

## Leaderboards And Model Introspection

Installed signature:

```python
predictor.leaderboard(
    data=None,
    extra_info=False,
    extra_metrics=None,
    decision_threshold=None,
    score_format="score",
    only_pareto_frontier=False,
    skip_score=False,
    refit_full=None,
    set_refit_score_to_parent=False,
    display=False,
    **kwargs,
)
```

Common columns include `model`, `score_val`, `eval_metric`, `pred_time_val`, `fit_time`, marginal times, `stack_level`, `can_infer`, and `fit_order`. When `data` with labels is provided, the output also includes test-score and test-latency columns. With `extra_info=True`, the leaderboard can include memory, feature, hyperparameter, ancestor, descendant, and model-type details.

Other useful introspection:

```python
predictor.model_names()
predictor.model_best
predictor.model_info(model)
predictor.info()
predictor.fit_summary(verbosity=3, show_plot=False)
predictor.model_hyperparameters(model, output_format="user")
predictor.model_refit_map()
```

## Feature Transformation And Importance

```python
predictor.transform_features(data=None, model=None, base_models=None, return_original_features=True)
predictor.transform_labels(labels, inverse=False, proba=False)
predictor.feature_importance(
    data=None,
    model=None,
    features=None,
    feature_stage="original",
    subsample_size=5000,
    time_limit=None,
    num_shuffle_sets=None,
    include_confidence_band=True,
    confidence_level=0.99,
    max_rows_per_batch=100000,
    max_memory_ratio=0.1,
    silent=False,
)
```

Feature importance is permutation-based and can be slower than fitting. Prefer held-out data with labels. `feature_stage` choices are:

- `"original"`: original input columns; requires `data`.
- `"transformed"`: global AutoGluon feature-generator output.
- `"transformed_model"`: features as seen by a specific model, including stack features where relevant.

## Model Management

```python
predictor.refit_full(model="all", set_best_to_refit_full=True, train_data_extra=None, num_cpus="auto", num_gpus="auto", fit_strategy="auto")
predictor.fit_extra(hyperparameters, time_limit=None, base_model_names=None, fit_weighted_ensemble=True, num_cpus="auto", num_gpus="auto", fit_strategy="auto", memory_limit="auto", **kwargs)
predictor.fit_weighted_ensemble(base_models=None, name_suffix="Best", expand_pareto_frontier=False, time_limit=None, refit_full=False, num_cpus="auto", num_gpus="auto")
predictor.persist(models="best", with_ancestors=True, max_memory=0.4)
predictor.unpersist(models="all")
predictor.compile(models="best", with_ancestors=True, compiler_configs="auto")
predictor.delete_models(models_to_keep=None, models_to_delete=None, allow_delete_cascade=False, delete_from_disk=True, dry_run=False)
predictor.save_space(remove_data=True, remove_fit_stack=True, requires_save=True, reduce_children=False)
```

Notes:

- `refit_full` creates `_FULL` models; validate them on held-out test data because refit-full models do not have validation scores.
- `fit_extra` uses the original cached train/tuning data and cannot change initial holdout/bagging/feature-generator choices.
- `persist` speeds online inference by keeping selected models and ancestors in memory; `unpersist` frees memory.
- `compile` is experimental and requires compiler-specific packages such as ONNX tooling.
- Always call `delete_models(..., dry_run=True)` before destructive deletion.
- `save_space` and deployment presets can disable later advanced analysis that depends on cached training data or out-of-fold predictions.

## Save And Load

```python
predictor.save(silent=False)
loaded = TabularPredictor.load(
    path,
    verbosity=None,
    require_version_match=True,
    require_py_version_match=True,
    check_packages=False,
)
```

`TabularPredictor.load` uses Python pickle internally. Load only predictor directories from trusted sources. For moved predictors:

1. Try strict loading first with the defaults.
2. If version or Python mismatches occur, inspect the environment and predictor metadata before relaxing checks.
3. Use `check_packages=True` to log package-version mismatches.
4. Relax `require_version_match` or `require_py_version_match` only for controlled compatibility testing, not routine production serving.

## Presets And Hyperparameter Presets

Current fit preset names include:

- Quality presets: `medium_quality`, `good_quality`, `high_quality`, `best_quality`, `extreme_quality`.
- Versioned/alias presets include `best_quality_v150`, `high_quality_v150`, aliases such as `medium`, `good`, `high`, `best`, `extreme`, and short aliases `mq`, `gq`, `hq`, `bq`, `eq`.
- Utility presets: `optimize_for_deployment`, `ignore_text`, `ignore_text_ngrams`, `interpretable`.

Current hyperparameter preset names include `default`, `light`, `very_light`, `toy`, `multimodal`, `interpretable`, `zeroshot`, `zeroshot_2023`, `zeroshot_2025_tabfm`, `zeroshot_2025_12_18_cpu`, `zeroshot_2025_12_18_gpu`, and `experimental`.

Use `toy` only for smoke tests; it trades away quality. Use `light` or `very_light` for faster/smaller models. Use `zeroshot` or v1.5 portfolios when accuracy and time budgets justify larger model search.
