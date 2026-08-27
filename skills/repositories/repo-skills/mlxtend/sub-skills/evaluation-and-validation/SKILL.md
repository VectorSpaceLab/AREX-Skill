---
name: evaluation-and-validation
description: "Use mlxtend.evaluate metrics, validation splitters, resampling
  procedures, model-comparison tests, permutation importance, and counterfactual
  helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# evaluation-and-validation

Use this sub-skill when the task is about evaluating predictions, choosing validation splits, comparing fitted estimators statistically, estimating uncertainty or feature importance, or creating counterfactual examples with `mlxtend.evaluate`.

## Read first

- [references/api-reference.md](references/api-reference.md) for verified `mlxtend.evaluate` signatures, return shapes, scorer contracts, and interpretation notes.
- [references/workflows.md](references/workflows.md) for decision recipes: metrics/scoring, holdout splitters, bootstrap/OOB/.632, permutation tests, paired model tests, F/McNemar/Cochran tests, permutation feature importance, and counterfactuals.
- [references/troubleshooting.md](references/troubleshooting.md) for common shape, scoring, `predict_proba`, method-name, time-series split, and resampling-cost failures.
- [scripts/evaluation_smoke.py](scripts/evaluation_smoke.py) to smoke-test the installed API on deterministic tiny CPU examples.

## Route here for

- `accuracy_score`, `scoring`, `confusion_matrix`, `lift_score`, and `proportion_difference` for prediction metrics and simple proportion tests.
- `bootstrap`, `BootstrapOutOfBag`, `bootstrap_point632_score`, `bias_variance_decomp`, and `permutation_test` for uncertainty, OOB/.632 validation, bias-variance checks, and nonparametric tests.
- `paired_ttest_resampled`, `paired_ttest_kfold_cv`, `paired_ttest_5x2cv`, `combined_ftest_5x2cv`, `ftest`, `mcnemar_table(s)`, `mcnemar`, and `cochrans_q` for model comparison.
- `RandomHoldoutSplit`, `PredefinedHoldoutSplit`, and `GroupTimeSeriesSplit` for sklearn-compatible validation splitters.
- `feature_importance_permutation` and `create_counterfactual` for evaluation-time interpretability helpers.

## Boundaries and sibling routes

- Do not construct or tune estimators here except as minimal evaluation examples. For mlxtend classifiers, regressors, stacking, voting, and Kmeans, read [../estimators-and-ensembles/SKILL.md](../estimators-and-ensembles/SKILL.md).
- Do not cover feature selection or extraction algorithms here. For selectors, PCA/LDA/kernel PCA, preprocessing, and transaction encoding, read [../feature-workflows/SKILL.md](../feature-workflows/SKILL.md).
- Do not use this sub-skill for plotting confusion matrices, split diagrams, learning curves, decision regions, or feature-importance charts. For visualization and utility helpers, read [../plotting-and-utilities/SKILL.md](../plotting-and-utilities/SKILL.md).

## Operating reminders

- Most estimator-based routines repeatedly call `fit` and `predict` or a sklearn scorer. Use fresh estimator instances when preserving fitted state matters.
- Set `random_seed` or `seed` for deterministic validation and keep `num_rounds`, `n_splits`, and exact permutation sizes small during exploration.
- Interpret `p` values against a predeclared significance level; a low p-value rejects the null hypothesis for the chosen test but does not rank models by practical effect size.
