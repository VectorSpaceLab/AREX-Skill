---
name: reductions
description: "Use Fairlearn reductions mitigation with ExponentiatedGradient,
  GridSearch, and Moment constraints for sklearn-compatible estimators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Fairlearn reductions

Use this sub-skill when the task asks to train or compare fairness-constrained models through reductions: `ExponentiatedGradient`, `GridSearch`, `Moment`, `DemographicParity`, `EqualizedOdds`, `BoundedGroupLoss`, sample weights, or sklearn-compatible estimators with `fit`/`predict`.

## Quick workflow

1. Pick a base estimator that supports `fit(X, y, sample_weight=...)` and `predict(X)`.
2. Pick a `Moment` constraint matching the fairness target.
3. Fit `ExponentiatedGradient` for iterative oracle-based mitigation or `GridSearch` for a finite grid of Lagrange multipliers.
4. Pass `sensitive_features=...` to `fit`.
5. Predict on held-out data.
6. Route to `../assessment/` to compare utility and disparity against a baseline estimator.

## Read these references

- [`references/workflows-and-api.md`](references/workflows-and-api.md) for algorithm choice, public signatures, constraint classes, sample-weight routing, and evaluation patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md) for estimator incompatibility, unsupported constraints, selection-rule errors, and pipeline metadata issues.
- [`scripts/smoke_reductions.py`](scripts/smoke_reductions.py) for a tiny CPU-only synthetic smoke check covering `ExponentiatedGradient` and `GridSearch`.

## Core APIs to recognize

- `ExponentiatedGradient(estimator, constraints, *, objective=None, eps=0.01, max_iter=50, nu=None, eta0=2.0, run_linprog_step=True, sample_weight_name="sample_weight")`
- `GridSearch(estimator, constraints, selection_rule="tradeoff_optimization", constraint_weight=0.5, grid_size=10, grid_limit=2.0, grid_offset=None, grid=None, sample_weight_name="sample_weight")`
- Classification constraints: `DemographicParity`, `EqualizedOdds`, `TruePositiveRateParity`, `FalsePositiveRateParity`, `ErrorRateParity`.
- Regression / loss constraints and objectives: `BoundedGroupLoss`, `SquareLoss`, `AbsoluteLoss`, `MeanLoss`, `ErrorRate`, `ZeroOneLoss`.

## Boundary rules

- This sub-skill owns mitigation during model training. Use `../postprocessing/` if the base predictor is already trained and only thresholds should change.
- Use `../preprocessing/` when the user wants to transform features before ordinary training.
- Use `../adversarial/` when the user wants neural-network adversarial training rather than reductions.
- Use `../assessment/` for grouped metric reporting, model-comparison plots, and validation tables.

## Operating rules

- Reductions use repeated calls to the base estimator. Keep base estimators deterministic when possible (`random_state`) so comparisons are reproducible.
- Confirm the estimator supports sample weights. If the argument name differs, set `sample_weight_name`.
- For sklearn `Pipeline` objects, use a routed sample-weight name such as `classifier__sample_weight` when the final step is named `classifier`.
- Keep `sensitive_features` out of `X` only if the modeling decision requires that; Fairlearn still needs the vector/matrix at `fit` time.
- Report trade-offs. A reduced model can lower a disparity metric while increasing error or changing selection rate.

## Fast validation

Run:

```bash
python sub-skills/reductions/scripts/smoke_reductions.py
```

The smoke uses sklearn and synthetic CPU data only.
