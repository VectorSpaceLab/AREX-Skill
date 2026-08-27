---
name: search-and-parallelism
description: "Control auto-sklearn search spaces, parallel resources, ensembles,
  disk outputs, and result-inspection APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Search and Parallelism

Use this sub-skill when the task is to configure or diagnose auto-sklearn search/resources, Dask parallelism, SMAC strategy callbacks, ensemble construction, disk outputs, or result inspection after a fit.

## Route here for

- Choosing `time_left_for_this_task`, `per_run_time_limit`, `memory_limit`, `n_jobs`, `dask_client`, thread-environment limits, `tmp_folder`, and disk-retention knobs.
- Restricting the search space with `include` or `exclude` dictionaries and built-in component IDs.
- Selecting SMAC behavior with `get_smac_object_callback`, `smac_scenario_args`, random search/ROAR, successive halving, or `get_trials_callback`.
- Planning single-machine `n_jobs` runs, attaching a user-created Dask client, or explaining the internal `LocalDask`/`UserDask` behavior.
- Designing sequential search followed by post-hoc `fit_ensemble()`.
- Controlling ensembles with `ensemble_class`, `ensemble_kwargs`, `ensemble_nbest`, `max_models_on_disc`, `disable_evaluator_output`, and `load_models`.
- Inspecting `sprint_statistics()`, `leaderboard()`, `show_models()`, `cv_results_`, `performance_over_time_`, `runhistory_`, and ensemble model weights.

## Route elsewhere

- Basic estimator selection, `fit`, `predict`, `predict_proba`, `score`, persistence, and minimal smoke workflows: [estimators](../estimators/SKILL.md).
- Data formats, train/test split semantics, resampling choices, metrics, custom scorers, and `refit()` requirements after CV/custom splits: [data-metrics-validation](../data-metrics-validation/SKILL.md).
- Writing or registering custom classifiers, regressors, preprocessors, or component search spaces: [custom-components](../custom-components/SKILL.md).
- Large metadata regeneration, `metadata_directory`, AutoSklearn2 portfolios, and maintenance scripts: [metadata-maintenance](../metadata-maintenance/SKILL.md).

## Fast operating checklist

1. Decide the workflow mode:
   - `sequential`: one worker; optionally set `ensemble_class=None` during search and call `fit_ensemble()` later.
   - `parallel`: set `n_jobs > 1` or pass a Dask `Client`; guard script entry points with `if __name__ == "__main__":`.
   - `random`: supply a `get_smac_object_callback` that returns a SMAC ROAR/random-search facade.
   - `successive-halving`: supply a `get_smac_object_callback` that returns `SMAC4AC(..., intensifier=SuccessiveHalving, ...)` and sets `ta_kwargs["budget_type"]`.
2. Budget resources conservatively. In multi-process search, total model-training memory can approach `n_jobs * memory_limit` plus the parent process and Dask overhead. If the dataset is large, do not simply raise `n_jobs`.
3. Set thread caps before Python starts when using multiple workers or when predicting/scoring large ensembles:
   ```bash
   export OPENBLAS_NUM_THREADS=1
   export MKL_NUM_THREADS=1
   export OMP_NUM_THREADS=1
   ```
4. If using Dask workers across processes or machines, ensure all workers can read/write the same `tmp_folder` and output area.
5. Choose `include`/`exclude` with valid component IDs. Use `include` for tight, interpretable, or fast searches; use `exclude` to remove only known bad/expensive components. Do not set both.
6. Keep evaluator output enabled unless the workflow is analysis-only and does not need prediction or ensembles. `disable_evaluator_output=True` disables saved models and predictions, so `predict()` is unavailable.
7. Inspect results in layers: `sprint_statistics()` for run counts, `leaderboard()` for tabular ranking, `show_models()` for ensemble members, `cv_results_` for GridSearchCV-like details, and `performance_over_time_` for time curves.

## Bundled references and helper

- [Search and parallelism reference](references/search-and-parallelism.md) — constructor parameters, include/exclude IDs, Dask patterns, SMAC callbacks, and search-mode snippets.
- [Results and ensembles reference](references/results-and-ensembles.md) — ensemble controls, disk outputs, `fit_ensemble()`, `leaderboard()`, `show_models()`, `cv_results_`, and `performance_over_time_`.
- [Troubleshooting reference](references/troubleshooting.md) — fork/forkserver/main-guard failures, memory and time limits, disk growth, Dask cleanup, and disabled evaluator outputs.
- [scripts/build_search_config.py](scripts/build_search_config.py) — safe snippet generator; emits JSON/Python configuration examples without importing or running auto-sklearn.

## Validation before a future run

- Print the generated constructor kwargs and verify there is no simultaneous `include` and `exclude`.
- Confirm `time_left_for_this_task >= 2 * per_run_time_limit` if an ensemble is expected; auto-sklearn may cap per-run time to leave room for at least two models.
- For parallel workflows, confirm code and data loading are inside a main guard or functions, shared storage is visible to workers, and user-owned Dask clients are closed by user code.
- For result inspection, verify `fit()` completed and evaluator output was not disabled in a way that removed required predictions/models.
