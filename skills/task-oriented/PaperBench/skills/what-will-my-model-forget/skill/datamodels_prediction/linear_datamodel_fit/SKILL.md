---
name: linear_datamodel_fit
description: Fit target-specific linear datamodel surrogates from subset membership vectors to observed target outcomes.
---

# Linear Datamodel Fit

Use this skill after subset-output pairs are available for a fixed target example. It preserves the paper mechanism of predicting `f_A(x; S')` from the binary characteristic vector of `S'`.

## Inputs

- Binary membership matrix `X` with one row per sampled subset.
- Outcome vector `y` with one value per subset.
- Optional ridge value for stable underdetermined fits.

## Outputs

- Datamodel weights `theta`.
- Intercept.
- Predictions and diagnostics: Pearson correlation, MSE, and optional weight correlation.

## Workflow

1. Validate row counts and binary membership values.
2. Add an intercept column.
3. Solve least squares or ridge-regularized normal equations.
4. Evaluate on held-out subsets, not only the fitted rows.
5. Use learned weights as datamodel embeddings or pass them to counterfactual scoring.

## Validation

Run:

```bash
python scripts/fit_datamodel.py --demo
python tests/test_fit_datamodel.py
```

## Limitations

This skill fits the surrogate only; it does not create the base training subsets or train the original task model.
