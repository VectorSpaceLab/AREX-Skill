# Results, ensembles, and disk output controls

This reference explains how to inspect a finished auto-sklearn run and how the ensemble and file-output knobs interact.

## Result-inspection surface

Use these methods after `fit()` succeeds:

| API | Return type | What it tells you |
|---|---|---|
| `sprint_statistics()` | string | Dataset name, metric(s), best validation score, run counts, crash/time/memory failures. |
| `leaderboard(detailed=False, ensemble_only=True, top_k='all', sort_by='cost', sort_order='auto', include=None)` | `pandas.DataFrame` | Tabular ranking of model runs, ensemble membership, and optional detailed columns. |
| `show_models()` | `dict[int, dict]` | Ensemble member details and the underlying wrapped sklearn objects. |
| `cv_results_` | `dict[str, array-like]` | GridSearchCV-like run history, model IDs, hyperparameters, scores, statuses, and budgets. |
| `performance_over_time_` | `pandas.DataFrame` | Running best single-model and ensemble performance over time. |
| `runhistory_` / `trajectory_` | SMAC objects | Low-level optimizer history and incumbent trajectory. Use these only when you need deeper debugging. |

### When each API is safe

- `leaderboard()` and `show_models()` require a fitted estimator and a live ensemble, unless you deliberately configured the workflow to build no ensemble.
- `predict()` and `predict_proba()` require a fitted estimator and normally require saved model artifacts to be available.
- `cv_results_` is unavailable for partial-cv modes and is best used after the main search has finished.
- `performance_over_time_` is most useful when you passed `X_test` and `y_test` to `fit()` so test scores can be tracked.

## Ensemble controls

### `ensemble_class`

- Default behavior uses `EnsembleSelection` for single-objective problems and a multi-objective dummy ensemble for multi-objective runs.
- Set `ensemble_class=None` to skip ensemble building during search. This is the right choice for sequential workflows that want search first and a separate `fit_ensemble()` later.
- You can also provide `SingleBest`-style behavior by choosing a single-model ensemble class if the user only wants the best fitted model.

### `ensemble_kwargs`

Pass extra constructor arguments to the selected ensemble class.

Common pattern:

```python
automl = autosklearn.classification.AutoSklearnClassifier(
    ensemble_kwargs={"ensemble_size": 20},
)
```

Legacy `ensemble_size=` still appears in the API, but future guidance should prefer `ensemble_kwargs={"ensemble_size": ...}` when the ensemble class is `EnsembleSelection`.

### `ensemble_nbest`

- Limits which evaluated models are considered for ensemble building.
- Can be an integer count or a fraction in the ensemble builder layer.
- Useful when many runs are present but only the top subset should contribute to the ensemble.

### `max_models_on_disc`

This is the main disk-growth limiter for model artifacts and their predictions.

- Integer: keep at most that many models on disk.
- Float in builder-level paths: interpreted as a memory budget for model files.
- `None`: disable the limit and keep everything.

Important interaction:

`ensemble_size`, `ensemble_nbest`, and `max_models_on_disc` jointly limit how many models can be used in the final ensemble. The tightest limit wins.

### `load_models`

- Default `True` loads fitted models into memory after `fit()`.
- Set to `False` when you only need run metadata or want to postpone loading until result inspection.
- If you later need `show_models()`, `predict()`, or ensemble-weight inspection, ensure models can still be loaded from disk.

## Disk-output controls

### `tmp_folder`

- Where temporary run artifacts, logs, and model files are written.
- Use a dedicated run directory for every run.
- When omitted, auto-sklearn creates a temporary directory automatically.

### `delete_tmp_folder_after_terminate`

- Default `True` removes the temporary run directory at the end.
- Set to `False` when you need post-run inspection or a later `fit_ensemble()` pass.

### `disable_evaluator_output`

This is the most important output-retention switch.

- `False`: keep ordinary model/prediction outputs.
- `True`: disable model and prediction output completely.
- Iterable/list mode: disable only selected artifacts such as `model`, `cv_model`, `y_optimization`, or `y_test`.

Rules:

- `True` means `predict()` is not available afterward.
- If model files are disabled, ensemble reconstruction and prediction-related inspection can fail or fall back to degraded behavior.
- Use list mode only when you intentionally want a partially retained run.
- In a narrow inspection-only task, prefer leaving evaluator output enabled and controlling disk use via `tmp_folder` and `max_models_on_disc` instead.

## Sequential search and post-hoc ensembles

A safe low-core workflow is:

1. Run search with `ensemble_class=None` so training focuses on model search.
2. Call `fit_ensemble(y_train, ...)` afterward to build the ensemble from saved runs.
3. Inspect the new ensemble with `show_models()` or `leaderboard(ensemble_only=True)`.

Example:

```python
automl = autosklearn.classification.AutoSklearnClassifier(
    time_left_for_this_task=1800,
    ensemble_class=None,
    delete_tmp_folder_after_terminate=False,
)
automl.fit(X_train, y_train, dataset_name="my_dataset")
automl.fit_ensemble(y_train, ensemble_class=EnsembleSelection)
print(automl.show_models())
```

Use this when users want to separate “search” and “ensemble building” phases or when they want a single-core search followed by explicit post-hoc ensembling.

## `leaderboard()` usage patterns

`leaderboard()` accepts filters and sort controls useful for investigation:

- `ensemble_only=True` to focus on ensemble members.
- `ensemble_only=False` to see all evaluated runs.
- `detailed=True` for more metadata columns.
- `include=` to select only a subset of columns.
- `sort_by='cost'` or a single column for ranking.
- `top_k=` to trim output.

Common result-debugging reads:

```python
leader = automl.leaderboard(ensemble_only=False, detailed=True, top_k=10)
summary = automl.leaderboard(ensemble_only=True)
```

Validation rules:

- `top_k` must be positive or `'all'`.
- `include` cannot be only `model_id`.
- Invalid column names raise `ValueError`.
- For multi-objective runs, cost ranking uses the first objective columns.

## `show_models()` output shape

`show_models()` returns a mapping keyed by `model_id`. Each value typically contains:

- `model_id`
- `rank`
- `cost`
- `ensemble_weight`
- `data_preprocessor`
- `feature_preprocessor`
- `classifier` or `regressor`
- `sklearn_classifier` or `sklearn_regressor`
- CV-only entries such as `voting_model` and `estimators`

Use this to answer “what is actually in the ensemble?” and to extract the underlying sklearn objects for further inspection.

## `cv_results_` and `performance_over_time_`

### `cv_results_`

The dict is designed to be turned into a pandas DataFrame.

Key fields include:

- `model_ids`
- `params`
- `status`
- `budgets`
- `mean_test_score` or per-metric names
- `rank_test_scores`
- `param_<hyperparameter>` masked arrays

Notes:

- Partial-CV modes do not support `cv_results_`.
- Some sklearn-style columns are intentionally absent, such as per-split scores or fit-time statistics.

### `performance_over_time_`

This DataFrame combines single-model progress and, when an ensemble exists, ensemble progress.

Columns commonly include:

- `Timestamp`
- `single_best_optimization_score`
- `single_best_test_score`
- `single_best_train_score`
- `ensemble_optimization_score`
- `ensemble_test_score`

Use it for over-time plots and to understand when the ensemble first improved over the best single model.

## Good inspection sequence

1. `print(automl.sprint_statistics())`
2. `automl.leaderboard(ensemble_only=False, detailed=True)`
3. `automl.show_models()`
4. `pd.DataFrame(automl.cv_results_)`
5. `automl.performance_over_time_.tail()`

If `predict()` fails after fit, first check whether evaluator output or model files were disabled.
