---
name: postprocessing
description: "Use Fairlearn ThresholdOptimizer and threshold-optimizer plots to
  adjust trained predictors under group fairness constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Fairlearn postprocessing

Use this sub-skill when the task asks to adjust a trained predictor's scores or predictions with group-specific thresholds: `ThresholdOptimizer`, `plot_threshold_optimizer`, `prefit`, `predict_method`, `tol`, demographic parity, equalized odds, false/true positive/negative rate parity, or threshold interpolation dictionaries.

## Quick workflow

1. Choose or fit a base estimator that exposes a useful score method: `predict_proba`, `decision_function`, or `predict`.
2. Create `ThresholdOptimizer(estimator=..., constraints=..., objective=..., predict_method=...)`.
3. Set `prefit=True` only when the estimator is already fitted and will not be cloned by cross-validation.
4. Fit the threshold optimizer with `sensitive_features=...`.
5. Predict with the same sensitive-feature grouping and, when deterministic output matters, pass `random_state` to `predict`.
6. Route to `../assessment/` to compare subgroup metrics before and after postprocessing.

## Read these references

- [`references/threshold-optimizer-workflows.md`](references/threshold-optimizer-workflows.md) for constructor options, constraints/objectives, `prefit`, score-method choice, plotting, and evaluation patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing base estimators, invalid constraint/objective combinations, plotting errors, `prefit` warnings, and data-layout failures.
- [`scripts/smoke_threshold_optimizer.py`](scripts/smoke_threshold_optimizer.py) for a tiny CPU-only synthetic smoke check with optional plotting.

## Core APIs to recognize

- `ThresholdOptimizer(*, estimator=None, constraints="demographic_parity", objective="accuracy_score", grid_size=1000, flip=False, prefit=False, predict_method="auto", tol=None)`
- `ThresholdOptimizer.fit(X, y, *, sensitive_features, **kwargs)`
- `ThresholdOptimizer.predict(X, *, sensitive_features, random_state=None)`
- `plot_threshold_optimizer(threshold_optimizer, ax=None, show_plot=True)`

## Boundary rules

- This sub-skill owns post-fit threshold/interpolation mitigation. Use `../reductions/` for fairness-constrained retraining and `../preprocessing/` for feature transformation.
- Use `../assessment/` for grouped metrics and model-comparison plots. `plot_threshold_optimizer` visualizes the postprocessor internals, not a full fairness report.
- Use `../installation/` or root troubleshooting when matplotlib is missing.
- Use `../adversarial/` for neural adversarial fairness; it is not a threshold optimizer.

## Operating rules

- `y` must be binary for `ThresholdOptimizer` in this source.
- `sensitive_features` are required for both `fit` and `predict`.
- Prefer `predict_proba` or `decision_function` over hard-label `predict` when meaningful scores are available.
- `equalized_odds` does not support `tol` relaxation in the inspected source.
- `prefit=True` is unsafe with estimator cloning workflows such as `cross_val_score` or `GridSearchCV`; use `prefit=False` there.
- Postprocessing can change output randomness. Use `random_state` in `predict` for reproducible reports.

## Fast validation

Run:

```bash
python sub-skills/postprocessing/scripts/smoke_threshold_optimizer.py
```

Run plot coverage in a matplotlib-capable environment:

```bash
python sub-skills/postprocessing/scripts/smoke_threshold_optimizer.py --plot --output-dir /tmp/fairlearn-threshold-plots
```
