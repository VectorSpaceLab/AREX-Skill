---
name: estimators
description: "Route feature-importance and learning-curve requests to
  scikitplot.estimators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Estimators

Use this sub-skill for the estimator-oriented plots in `scikitplot.estimators`: feature importances and learning curves.

## Route here

- Plot feature importances from a fitted estimator that exposes `feature_importances_`.
- Plot learning curves from an estimator plus `X`, `y`, CV choices, and scoring settings.
- Reuse or compose Matplotlib axes with `ax=`; both functions return the axes they drew on.
- Validate the route quickly with `scripts/estimators_smoke.py`.

## Reroute

- Confusion matrix, ROC, precision-recall, KS, calibration, cumulative gain, lift, or silhouette: `../metrics/SKILL.md`.
- Elbow-curve workflows or clusterer-specific routing: `../clustering/SKILL.md`.
- Bound-method wrappers from the legacy factory layer, including injected estimator methods: `../legacy-factories/SKILL.md`.
- PCA or other dimensionality-reduction plots: not handled here.

## Start fast

1. Confirm the estimator contract.
   - `plot_feature_importances` requires `feature_importances_`.
   - `plot_learning_curve` passes an estimator through `sklearn.model_selection.learning_curve`.
2. Pick the right options.
   - `order` accepts only `ascending`, `descending`, or `None`.
   - `cv`, `shuffle`, `random_state`, `train_sizes`, `n_jobs`, and `scoring` are forwarded to `learning_curve`.
3. Reuse axes explicitly when composing figures.
4. Run the smoke script for a tiny deterministic check:

```bash
python scripts/estimators_smoke.py
```

## References

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/estimators_smoke.py`
