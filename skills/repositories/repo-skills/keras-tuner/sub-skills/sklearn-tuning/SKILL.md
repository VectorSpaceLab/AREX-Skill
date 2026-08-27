---
name: sklearn-tuning
description: "Routes KerasTuner SklearnTuner workflows for conditional
  scikit-learn estimator factories, cross-validation, scoring, groups, sample
  weights, DataFrame inputs, and pickle-backed model recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Scikit-learn tuning

Use this sub-skill when the task is about `keras_tuner.SklearnTuner`, tuning a
scikit-learn estimator factory, cross-validating several estimator families, or
restoring a tuned estimator from a KerasTuner trial. This route is for
scikit-learn models, not Keras neural-network training.

## Include here

- `SklearnTuner(oracle, hypermodel, scoring=None, metrics=None, cv=None, **kwargs)`.
- Conditional `HyperParameters` factories that return classifiers, regressors,
  or scikit-learn `Pipeline` objects.
- A consistent explicit scorer when model families have different default
  `score` semantics.
- Custom cross-validation splitters, `groups`, and `sample_weight`.
- NumPy and optional pandas DataFrame inputs.
- `get_best_models()` / `load_model()` recovery of `model.pickle` artifacts.
- Diagnosing invalid input types and absent optional dependencies.

## Exclude or route elsewhere

- Keras model training, neural-specific callbacks, and epoch-budget search →
  the parent tuning route.
- Distributed chief/worker coordination → the distributed-tuning route.
- Image hypermodel constructors → the image-hypermodels route.
- `Hyperband`: it is a neural-training oracle and is not an appropriate Oracle
  for `SklearnTuner`.

## Fast route

1. Confirm scikit-learn is installed; install pandas too if DataFrames are
   required.
2. Build one estimator per trial from `hp`, using conditional scopes for
   branch-specific hyperparameters.
3. Create a non-neural Oracle with objective
   `keras_tuner.Objective("score", "max")`; Bayesian optimization is a good
   default for a small space.
4. Supply an explicit `scoring` callable when comparing model families, then
   select `cv` and pass `groups` when the splitter requires them.
5. Call `search(X, y, sample_weight=..., groups=...)` with NumPy arrays or
   pandas DataFrames and inspect trial status/metrics.
6. Restore the winner with `get_best_models()` and validate it on held-out
   data. See [workflows](references/workflows.md).

## Read next

- [API reference](references/api-reference.md) for exact signatures and
  implementation-backed behavior.
- [Workflows](references/workflows.md) for factory, scoring, CV, weighting,
  DataFrame, and restore patterns.
- [Troubleshooting](references/troubleshooting.md) for dependency and input
  failures.
- From the skill root, run `sub-skills/sklearn-tuning/scripts/smoke_sklearn.py` for a tiny dependency-aware local check.

## Operating cautions

- `cv=None` means `KFold(5, shuffle=True, random_state=1)`.
- `sample_weight` is split per fold. It is passed to an estimator's `fit` only
  when `fit` advertises `sample_weight`; it is omitted for a scikit-learn
  `Pipeline` and estimators without that argument.
- The tuner saves only the model produced by the final CV fold for each trial,
  although the trial score is the mean over folds. Treat it as the refit model
  only after checking the intended deployment workflow.
- DataFrame support depends on pandas being importable when the tuner module is
  loaded. Plain lists are not accepted as `X` or `y`.
