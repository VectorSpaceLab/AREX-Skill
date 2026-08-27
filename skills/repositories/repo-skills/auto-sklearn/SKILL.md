---
name: auto-sklearn
description: "Route auto-sklearn AutoML estimator, data validation, search,
  custom component, and metadata-maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# auto-sklearn

Use this repo skill when the task names `auto-sklearn`, `autosklearn`, `AutoSklearnClassifier`, `AutoSklearnRegressor`, `AutoSklearn2Classifier`, autoML/HPO search, auto-sklearn metrics, component extension, or auto-sklearn metadata maintenance. Start here, then load the narrowest sub-skill for the requested workflow.

## Quick install and import check

`auto-sklearn` is a Linux-oriented Python package with compiled dependencies. In a clean environment, install the public package or the user's selected source distribution, then verify the same Python that will run the task:

```bash
python -m pip install auto-sklearn
python -m pip check
python -I -c "import autosklearn; print(autosklearn.__version__)"
python -I -c "import autosklearn.classification, autosklearn.regression, autosklearn.metrics"
```

If pip builds dependencies from source, the environment may need a C++11 compiler and SWIG. For import errors, compiled dependency failures, unsupported OS/Python, `pkg_resources` warnings, or ConfigSpace/NumPy ABI problems, read [cross-cutting troubleshooting](references/troubleshooting.md) before routing deeper.

Read [repository provenance](references/repo-provenance.md) when checking whether this generated skill is current for a checkout or installed package version. The router metadata consumed by managed imports is in [repo-routing-metadata.json](references/repo-routing-metadata.json).

## Workflow lanes

| User need | Read |
|---|---|
| Choose classifier vs regressor vs AutoSklearn2, call `fit`, `predict`, `predict_proba`, `refit`, `fit_ensemble`, inspect `sprint_statistics`, or run a bounded smoke helper | [estimators](sub-skills/estimators/SKILL.md) |
| Prepare pandas/NumPy/sparse/list inputs, diagnose `feat_type`, target encoding, `allow_string_features`, `dataset_compression`, built-in/custom metrics, `scoring_functions`, holdout/CV/custom splitters, or refit-after-CV rules | [data-metrics-validation](sub-skills/data-metrics-validation/SKILL.md) |
| Configure search budgets, `include`/`exclude`, `n_jobs`, Dask clients, thread limits, SMAC/random/successive-halving callbacks, ensembles, `leaderboard`, `show_models`, `cv_results_`, or `performance_over_time_` | [search-and-parallelism](sub-skills/search-and-parallelism/SKILL.md) |
| Implement or repair custom classifiers, regressors, feature/data preprocessors, ConfigSpace hyperparameters, component property dictionaries, registry calls, or custom component IDs | [custom-components](sub-skills/custom-components/SKILL.md) |
| Maintain meta-learning metadata, `metadata_directory`, AutoSklearn2 selector/portfolio context, ASLib files, metadata-generation scripts, `automl_common` submodule checks, or focused repository tests | [metadata-maintenance](sub-skills/metadata-maintenance/SKILL.md) |

## First-response patterns

- **Ordinary model-fitting request:** load `estimators`; if inputs or metrics are underspecified, also load `data-metrics-validation` before writing code.
- **Validation or scorer error:** load `data-metrics-validation` first. Do not start an AutoML fit just to validate containers or scorer flags.
- **Slow, memory-heavy, parallel, or dummy-only run:** load `search-and-parallelism`; use `estimators` for high-level dummy-only triage if the user only needs fit/predict recovery.
- **Search-space filtering:** load `search-and-parallelism` for built-in IDs and budget trade-offs; load `custom-components` if the user is adding a new component class.
- **AutoSklearn2 issue:** load `estimators` for use-level ASKL2 behavior; load `metadata-maintenance` for selector/portfolio/cache/metadata internals.
- **Repository contributor task:** load `metadata-maintenance` for metadata scripts, submodule state, and focused test guidance; load `custom-components` only for component API changes.

## Common signals and what they usually mean

| Signal | Likely lane |
|---|---|
| `feat_type`, pandas categories, datetime columns, target NaNs, custom scorers, `dataset_compression`, or custom splitters | `data-metrics-validation` |
| `n_jobs`, Dask, `include`/`exclude`, `ensemble_class`, `max_models_on_disc`, `leaderboard`, `show_models`, `performance_over_time_`, or main-guard/resource problems | `search-and-parallelism` |
| `AutoSklearnClassifier`, `AutoSklearnRegressor`, `AutoSklearn2Classifier`, `predict_proba`, `refit`, `fit_ensemble`, `sprint_statistics`, or dummy-only output | `estimators` |
| `add_classifier`, `add_regressor`, `add_preprocessor`, `get_properties`, ConfigSpace, or custom class IDs | `custom-components` |
| `metadata_directory`, selector cache, ASLib outputs, `scripts/01_create_commands.py`, `automl_common`, or repo test selection | `metadata-maintenance` |

## Minimal operating habits

1. Keep the task-specific lane narrow. If a task crosses lanes, resolve data/metric questions before search/fit questions and search questions before component-extension questions.
2. Verify the public package version and import surface before using version-sensitive arguments. This skill was built from `auto-sklearn` `0.16.0.dev0` / `0.16.0dev` evidence.
3. Use the bundled helper scripts under the relevant sub-skill for safe checks or command planning. Do not run the original repository's large examples or metadata scripts as the default runtime path.
4. Treat short smoke runs as plumbing checks only. They prove import, fit, inspect, and predict behavior, not model quality.
5. For source-maintenance work, check the `autosklearn/automl_common` submodule and dirty-tree state before changing metadata scripts or focused tests.

## Guardrails for future agents

- Keep `autosklearn` package guidance version-aware. Recheck live signatures before using parameters not shown in this skill, especially `output_directory`.
- Do not run original repo examples or metadata scripts as normal skill usage. Use bundled helper scripts under the relevant sub-skill, or ask before expensive/network/long-running native workflows.
- Do not treat a short AutoML smoke as model-quality evidence. It proves import, fit, inspect, and predict plumbing only.
- Keep data validation, metric design, and resampling decisions explicit before expensive fitting.
- For parallel runs, plan for `n_jobs * memory_limit` and require a Python main guard in scripts.
- For source-maintenance tasks, check submodule state and dirty-tree effects before and after focused tests.
