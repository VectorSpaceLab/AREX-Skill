# Estimator troubleshooting

Use this reference for high-level estimator failures. Route data format/metric/resampling problems to [data-metrics-validation](../../data-metrics-validation/), parallel/search/ensemble internals to [search-and-parallelism](../../search-and-parallelism/), custom components to [custom-components](../../custom-components/), and metadata refresh or ASKL2 metadata internals to [metadata-maintenance](../../metadata-maintenance/).

## Quick triage checklist

1. Can Python import `autosklearn`, `autosklearn.classification`, `autosklearn.regression`, and the chosen estimator class?
2. Does the installed estimator signature match the code being run? In the inspected 0.16.0dev API, estimator constructors do not accept `output_directory`.
3. Is the target type compatible with the chosen estimator? Probe with `sklearn.utils.multiclass.type_of_target(y)`.
4. Did `fit` finish with at least one successful target algorithm run in `sprint_statistics()`?
5. Is `disable_evaluator_output` `False`, and are `load_models=True` and saved output available when predicting, inspecting, refitting, or rebuilding ensembles?
6. Is the temporary folder unique, writable, and large enough for logs, predictions, and model files?
7. If the final ensemble is dummy-only, are `time_left_for_this_task`, `per_run_time_limit`, and `memory_limit` too tight?

## Install/import warnings and dependency compatibility

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError: No module named 'autosklearn'` | Package is not installed in the active Python environment. | Install/activate an environment that contains `autosklearn`; then re-run a simple import probe before using this skill. |
| Import errors involving `pyrfr`, compiled extensions, or segmentation faults | Missing/incorrect compiled dependency, C++ compiler, or SWIG during install; incompatible binary wheel. | Use a supported Linux/Python environment, install build dependencies, and test `import pyrfr.regression as reg; reg.default_data_container(64)`. If this fails, repair the dependency before estimator work. |
| Errors or warnings about unsupported OS/Python versions | auto-sklearn is Linux-oriented and has tight dependency constraints. | Prefer Linux with a package-supported Python/scikit-learn/ConfigSpace stack. Avoid assuming macOS/Windows or arbitrary new Python versions work. |
| ConfigSpace/NumPy ABI errors | Binary incompatibility between compiled ConfigSpace and NumPy. | Reinstall compatible package versions in a clean environment. Do not expose local environment paths in runtime instructions. |
| `pkg_resources` deprecation warning during import | The inspected package imports `pkg_resources` through dependency/version checks; newer setuptools may warn. | Treat as a warning if imports and estimator calls work. Pin/adjust packaging only if it becomes an error in the user's environment. |

## Wrong estimator or target shape

| Symptom | Cause | Fix |
|---|---|---|
| `Classification with data of type continuous is not supported` | Regression target passed to `AutoSklearnClassifier`. | Use `AutoSklearnRegressor`. |
| `Classification with data of type multiclass-multioutput/continuous-multioutput is not supported` | Multioutput target passed to classifier. | Use `AutoSklearnRegressor` for `continuous-multioutput`; true multiclass-multioutput is not supported by the standard estimator APIs. |
| `Regression with data of type multilabel-indicator is not supported` | Multilabel classification target passed to regressor. | Use `AutoSklearnClassifier` and keep a 2-D indicator target. |
| `predict_proba` missing or inappropriate | Regressor selected, or classifier output disabled/not fitted. | Use classifier for probabilities; confirm `fit` completed and evaluator output was not disabled. |
| Multilabel probabilities do not sum to 1 by row | Expected behavior: probabilities are per label. | Validate values are in `[0, 1]`; do not require row sums for multilabel-indicator targets. |

For pandas dtypes, categorical/string behavior, sparse inputs, target encoding, and `feat_type` errors, use [data-metrics-validation](../../data-metrics-validation/).

## Dummy-only or failed runs

A final ensemble containing only a dummy model means all started AutoML runs failed or no useful model completed. The FAQ identifies too-tight runtime or memory limits as the usual cause.

Signals:

- `show_models()` or `leaderboard()` shows only dummy-like entries or no meaningful ensemble members.
- `sprint_statistics()` reports zero successful target algorithm runs or mostly crashed/time-limit/memory-limit runs.
- Logs in the `tmp_folder` contain cutoff, memory, or crash messages.
- Scores are near dummy baselines, e.g. R2 around `0` or negative for regression where better performance is expected.

Actions:

1. Print and read `automl.sprint_statistics()` first.
2. Increase `time_left_for_this_task` and `per_run_time_limit`; the per-run limit must allow at least simple scikit-learn models to fit.
3. Increase `memory_limit` when crashes or memory-limit failures dominate.
4. Keep `tmp_folder` and set `delete_tmp_folder_after_terminate=False` for one diagnostic rerun so logs are available.
5. Reduce data size only for a smoke/debug run, not as a hidden change to the user's real task.
6. If the request involves search-space restrictions or parallelism, route to [search-and-parallelism](../../search-and-parallelism/) to avoid accidentally excluding every viable model or overcommitting resources.

## No fitted model or prediction fails after output was disabled

`disable_evaluator_output=True` disables model and prediction output. The estimator source warns it cannot be used together with ensemble building and `predict()` cannot be used when model/prediction files are not saved.

Signals:

- `predict` or `predict_proba` fails after `fit` even though the fit seemed to complete.
- `show_models()` or `fit_ensemble()` cannot locate models or predictions.
- The code used `disable_evaluator_output=True` or a list that omitted required outputs such as model files or optimization predictions.

Fix:

```python
automl = autosklearn.classification.AutoSklearnClassifier(
    time_left_for_this_task=300,
    per_run_time_limit=60,
    disable_evaluator_output=False,
    load_models=True,
)
automl.fit(X_train, y_train, dataset_name="my_dataset")
pred = automl.predict(X_test)
```

If the user intentionally disabled output to save disk, explain the trade-off: they can inspect some run records, but normal prediction/ensemble workflows require saved model or prediction files.

## Temporary folder and disk growth

Auto-sklearn writes logs, data manager files, model files, validation/test predictions, SMAC outputs, and ensemble artifacts to a temporary run directory. If `tmp_folder` is omitted, a system temporary directory with an `autosklearn_tmp_...` name is used and normally deleted after fitting.

Common issues and actions:

| Symptom | Cause | Action |
|---|---|---|
| Disk fills during fit | Many models/predictions/logs retained; parallel runs can temporarily exceed limits. | Set a dedicated `tmp_folder` on a volume with space; lower `max_models_on_disc`; use shorter diagnostic runs. |
| Cannot inspect logs after fit | Default cleanup deleted the temporary folder. | Re-run with `delete_tmp_folder_after_terminate=False` and explicit `tmp_folder`. |
| New run collides with old files | Reused `tmp_folder` from another run/seed. | Use a unique folder per independent run. Clean deliberately only after confirming no needed artifacts remain. |
| `output_directory` rejected as unexpected argument | The active estimator constructor lacks that parameter. | Remove `output_directory`; use `tmp_folder` for inspected 0.16.0dev API or recheck the active installed signature before using version-specific output arguments. |

## `leaderboard` and `show_models` surprises

| Symptom | Cause | Fix |
|---|---|---|
| `leaderboard(top_k=0)` or negative `top_k` raises `ValueError` | `top_k` must be positive or `'all'`. | Use `top_k=5` or `top_k='all'`. |
| `leaderboard(sort_order=None)` raises `ValueError` | Sort order must be `'auto'`, `'ascending'`, or `'descending'`. | Use the allowed strings. |
| `leaderboard(include='model_id')` raises `ValueError` | `model_id` is always the index and cannot be the only requested column. | Include at least one data column, e.g. `include=['model_id', 'rank', 'cost', 'type']`. |
| `leaderboard(ensemble_only=True)` is empty | No final ensemble members or no positive weights. | Try `ensemble_only=False`; inspect `sprint_statistics()` and run failures. |
| `show_models()` returns CV-shaped entries instead of direct `classifier`/`regressor` keys | Cross-validation resampling stores a `voting_model` and per-fold `estimators`. | Inspect keys conditionally; call `refit` before predicting on new data if needed. |

## Refit and post-hoc ensemble issues

| Symptom | Likely cause | Action |
|---|---|---|
| Predicting after CV says models are not fitted for new data | CV trained fold models and did not keep a single final model. | Call `automl.refit(X_train_full, y_train_full)`, then predict. |
| `fit_ensemble` fails or cannot find predictions | Previous fit did not save required prediction/model files, `tmp_folder` was deleted, or output was disabled. | Re-run with `delete_tmp_folder_after_terminate=False`, `disable_evaluator_output=False`, and enough disk; then call `fit_ensemble`. |
| Deprecation warning for `ensemble_size` | Direct `ensemble_size` argument is deprecated in the inspected API. | Use `ensemble_kwargs={"ensemble_size": n}` for ensemble selection. |

## AutoSklearn2Classifier cache and selector issues

ASKL2 creates or reuses selector files using packaged training data and the installed auto-sklearn/scikit-learn versions. It writes them under a cache location based on `XDG_CACHE_HOME` or the user's home directory.

| Symptom | Cause | Action |
|---|---|---|
| Permission error while constructing `AutoSklearn2Classifier` | Selector cache directory is not writable. | Set `XDG_CACHE_HOME` to a writable directory for the process, or use `AutoSklearnClassifier`. |
| User wants explicit `include`, `exclude`, or resampling in ASKL2 | ASKL2 does not expose those standard constructor knobs. | Use `AutoSklearnClassifier` with explicit settings, then route search details to [search-and-parallelism](../../search-and-parallelism/). |
| Metadata refresh question | ASKL2 selector/portfolio metadata generation is a maintenance workflow. | Route to [metadata-maintenance](../../metadata-maintenance/). |

## Safe bounded smoke troubleshooting

The bundled helper defaults to dry-run mode and prints planned actions. It performs a real AutoML fit only with `--run`.

| Symptom | Meaning | Action |
|---|---|---|
| `--help` fails | Script or Python syntax/import problem before runtime use. | Fix the helper before skill verification. |
| Dry-run works but `--run` import fails | auto-sklearn is not installed in the active Python environment. | Activate/install a compatible environment; rerun `--help` and then a bounded `--run` only if approved. |
| `--run` completes with dummy-only warnings | Budget was too small or environment/resource constraints blocked real models. | Increase `--time-left`, `--per-run-time-limit`, and possibly estimator memory; do not treat the smoke as model-quality proof. |
| Temporary smoke artifacts remain | `--tmp-dir` was supplied and the helper preserves it for inspection. | Delete the smoke directory after checking logs if no longer needed. |
