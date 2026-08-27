---
name: tuning
description: "Routes generic KerasTuner search workflows for HyperParameters,
  HyperModel, Oracle, Tuner, RandomSearch, GridSearch, Hyperband,
  BayesianOptimization, reload/resume, and custom black-box tuning loops."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tuning

Use this sub-skill when the task is about defining a hyperparameter search space, choosing a search algorithm, subclassing `Tuner` or `HyperModel`, inspecting trials, or resuming a saved search project.

## Include here

- `HyperParameters` search-space design.
- `HyperModel.build()` and `HyperModel.fit()`.
- `BaseTuner` / `Tuner` subclassing for custom objectives or nonstandard loops.
- `RandomSearch`, `GridSearch`, `Hyperband`, and `BayesianOptimization`.
- Trial inspection, `search_space_summary()`, `results_summary()`, `get_best_models()`, and `get_best_hyperparameters()`.
- Save/reload behavior for search projects.

## Exclude or route elsewhere

- `SklearnTuner` and estimator pipelines → `sub-skills/sklearn-tuning`.
- `HyperResNet`, `HyperXception`, `HyperEfficientNet`, `HyperImageAugment` → `sub-skills/image-hypermodels`.
- `KERASTUNER_ORACLE_*` env vars and chief/worker orchestration → `sub-skills/distributed-tuning`.

## Quick workflow

1. Define the search space with `hp.Choice`, `hp.Int`, `hp.Float`, `hp.Boolean`, or `hp.Fixed`.
2. Build a Keras model in `build_model(hp)` or a `HyperModel` subclass.
3. Choose a tuner:
   - `RandomSearch` for a baseline.
   - `GridSearch` for finite, exhaustive coverage.
   - `Hyperband` for budgeted training with early stopping.
   - `BayesianOptimization` for a smaller search space with expensive evaluations.
4. Call `search(...)` with training and validation data.
5. Read back the top trials and optionally `save()` / `reload()` the project.

## When this route is the right one

- The user says "tune this model", "search hyperparameters", "find the best architecture", or "resume a KerasTuner search".
- The user wants to subclass `Tuner` to optimize a black-box score or custom training loop.
- The user wants to understand `GridSearch` coverage, `Hyperband` rounds, or Bayesian trial selection.

## Read next

- `references/workflows.md` for small end-to-end search examples and restart patterns.
- `references/api-reference.md` for verified signatures and algorithm differences.
- `references/troubleshooting.md` for build, retry, and dependency errors.
- `sub-skills/tuning/scripts/smoke_search.py` when you want a tiny local search smoke test.

## Practical notes

- `Tuner.run_trial()` may return a `History`, a float, a dictionary, or a list of those values.
- `GridSearch` only fully exhausts finite search spaces.
- `Hyperband` injects `tuner/trial_id`, `tuner/initial_epoch`, and `tuner/epochs` during later rounds.
- `BayesianOptimization` requires SciPy and scikit-learn at construction time.
- The TensorFlow-backed 1.4.8 trial path imports TensorBoard's HParams API; install `tensorboard` before running Keras model searches.
- `save()` and `reload()` persist the project under `directory/project_name`.

## Troubleshooting checklist

- If `build(hp)` does not return a Keras model, `Tuner` raises a fatal type error.
- If the search is retrying unexpectedly, check whether your code raises `FailedTrialError` or a generic exception.
- If `GridSearch` ends early, make sure the relevant hyperparameters have finite values.
- If a search is very slow, reduce the synthetic data size or the number of trials before debugging the full workflow.
