---
name: estimators-and-ensembles
description: "Use mlxtend sklearn-style classifiers, regressors, Kmeans, voting
  ensembles, and stacking meta-estimators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# estimators-and-ensembles

Use this sub-skill when a task needs to construct, fit, tune, or diagnose `mlxtend.classifier`, `mlxtend.regressor`, or `mlxtend.cluster` estimators and ensemble meta-estimators.

## Read first

- [references/api-reference.md](references/api-reference.md) for verified constructor signatures, estimator methods, sample-weight behavior, meta-feature attributes, and sklearn parameter names.
- [references/workflows.md](references/workflows.md) for concrete recipes covering soft/hard voting, stacking classification, stacking regression, classic iterative estimators, linear regression, and Kmeans.
- [references/troubleshooting.md](references/troubleshooting.md) for `predict_proba`, `sample_weight`, `GridSearchCV`, unfitted/shape, label, convergence, and learning-rate failures.
- [scripts/estimator_ensemble_smoke.py](scripts/estimator_ensemble_smoke.py) to smoke-test installed estimator APIs on deterministic tiny CPU data.

## Route here for

- `EnsembleVoteClassifier` hard/soft voting, voting weights, prefit base estimators, sklearn `GridSearchCV`, and classifier probability aggregation.
- `StackingClassifier` and `StackingCVClassifier`, including `use_probas`, `drop_proba_col`, `average_probas`, `use_features_in_secondary`, `store_train_meta_features`, cross-validation, `groups`, clone/refit decisions, and meta-classifier tuning.
- `StackingRegressor` and `StackingCVRegressor`, including out-of-fold meta-features, multi-output targets, `refit`, `use_features_in_secondary`, and prefixed base/meta regressor parameters.
- Classic mlxtend estimators: `Adaline`, `Perceptron`, `LogisticRegression`, `SoftmaxRegression`, `MultiLayerPerceptron`, `OneRClassifier`, `LinearRegression`, and `Kmeans`.
- sklearn-style decisions around `fit`, `predict`, `predict_proba`, `predict_meta_features`, `get_params`, `set_params`, `cross_val_score`, and `GridSearchCV`.

## Boundaries and sibling routes

- Do not decide evaluation metrics, statistical model-comparison tests, bootstrap procedures, or validation splitters here except as minimal estimator examples. For those, read [../evaluation-and-validation/SKILL.md](../evaluation-and-validation/SKILL.md).
- Do not cover feature selectors, preprocessing transformers, PCA/LDA/kernel PCA, `TransactionEncoder`, or column-selection pipelines in depth. For those, read [../feature-workflows/SKILL.md](../feature-workflows/SKILL.md).
- Do not cover decision-region plots, confusion-matrix plots, learning curves, or Matplotlib utility behavior here. For visualization and utilities, read [../plotting-and-utilities/SKILL.md](../plotting-and-utilities/SKILL.md).

## Operating reminders

- Prefer sklearn estimators for base learners in ensembles unless you specifically need mlxtend's educational iterative implementations; clone-compatible sklearn estimators make `GridSearchCV` and cross-validation safer.
- For soft voting or probability-based stacking, every probability-producing base estimator used for meta-features must implement `predict_proba`; the final meta-classifier must implement `predict_proba` only if the downstream call needs probabilities.
- Use `StackingCVClassifier` or `StackingCVRegressor` when avoiding training-set leakage in meta-features matters; standard stacking fits level-2 models on predictions from base models trained on the same data.
- Keep task-specific scoring, plotting, and feature engineering in sibling sub-skills; this sub-skill owns estimator construction, fitting, prediction, and sklearn integration decisions.
