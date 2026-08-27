---
name: estimators
description: "Choose and use AutoSklearn estimator classes for fit, predict,
  refit, model inspection, temporary folders, and bounded smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# estimators

Use this sub-skill when the user needs to choose or operate the high-level estimator API: `AutoSklearnClassifier`, `AutoSklearnRegressor`, or `AutoSklearn2Classifier`; fit a model; predict or predict probabilities; refit or rebuild an ensemble; inspect basic run statistics, leaderboard rows, or final models; control temporary run folders; or run a bounded local smoke helper.

## Fast routing

- Binary, multiclass, or multilabel classification: use `autosklearn.classification.AutoSklearnClassifier` unless the user explicitly wants Auto-sklearn 2.0's hands-free classifier behavior.
- Regression or multioutput regression: use `autosklearn.regression.AutoSklearnRegressor`.
- Auto-sklearn 2.0 classification: use `autosklearn.experimental.askl2.AutoSklearn2Classifier` when the user wants ASKL2's selector/portfolio defaults and does not need explicit `include`, `exclude`, `resampling_strategy`, `metadata_directory`, or SMAC callback knobs.
- If the request is mostly about feature dtypes, `feat_type`, target validation, metrics, custom scorers, `dataset_compression`, or resampling strategies, route to [data-metrics-validation](../data-metrics-validation/).
- If the request is mostly about `n_jobs`, Dask, SMAC/search strategy, ensemble tuning, `performance_over_time_`, deep `cv_results_` interpretation, or disk/performance trade-offs, route to [search-and-parallelism](../search-and-parallelism/).
- If the request is about adding classifiers, regressors, preprocessors, component IDs, or search-space implementation, route to [custom-components](../custom-components/).
- If the request is about meta-learning metadata, ASKL2 selector files, `metadata_directory`, or metadata refresh, route to [metadata-maintenance](../metadata-maintenance/).

## Read first

- [API reference](references/api-reference.md) for imports, observed signatures, constructor knobs, target support, and post-fit inspection methods.
- [Workflows](references/workflows.md) for concrete classification, regression, multilabel, multioutput, refit, ensemble, folder-control, and bounded-smoke recipes.
- [Troubleshooting](references/troubleshooting.md) for import/install warnings, dummy-only ensembles, disabled-output prediction failures, temporary-folder growth, and ASKL2 cache issues.

## Minimal operating checklist

1. Select the estimator class from the target type and requested behavior.
2. Set explicit bounded resources: `time_left_for_this_task`, `per_run_time_limit`, `memory_limit` if needed, `seed`, and a unique `tmp_folder` when logs/models should be inspectable.
3. Call `fit(X_train, y_train, X_test=None, y_test=None, feat_type=None, dataset_name="short_name")`. Keep `dataset_name` short and non-sensitive; it improves statistics and output labeling.
4. Validate outputs immediately after fit:
   - classifier: `predict(X_test)` shape matches expected target shape; `predict_proba(X_test)` values are in `[0, 1]` and non-multilabel rows sum to 1.
   - regressor: `predict(X_test)` shape is `(n_samples,)` or `(n_samples, n_outputs)` for multioutput regression.
5. Inspect the run with `sprint_statistics()`, `leaderboard(...)`, and `show_models()` before deciding whether the result is meaningful. A dummy-only final ensemble is a troubleshooting signal, not a success.
6. Use `refit(X, y)` after cross-validation or when the final ensemble should be trained on all available training data. Use `fit_ensemble(...)` only when model/prediction outputs were saved.
7. For a safe smoke, run `python sub-skills/estimators/scripts/bounded_estimator_smoke.py --help` or dry-run the helper first; add `--run` only when a bounded AutoML fit is acceptable.

## Guardrails

- Do not pass `output_directory` to these estimator constructors for the inspected 0.16.0dev API: it is not in the observed public estimator signatures. Prefer `tmp_folder` plus `delete_tmp_folder_after_terminate`; verify a newer installed signature before using any documented `output_directory` variant.
- Do not set `disable_evaluator_output=True` when the user expects `predict`, `predict_proba`, `show_models`, or post-hoc `fit_ensemble` to work.
- Do not reuse an old temporary run folder for a new independent fit unless the user intentionally wants to resume/inspect a prior run and the folder semantics are understood.
- Do not claim that a very small smoke budget proves model quality. It only proves that the estimator API can import, fit, inspect, and predict on a small dataset.
