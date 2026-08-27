---
name: "probabilistic-losses"
description: "Routes NeuralForecast quantile, distribution, robust-loss, and
  prediction-interval workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# probabilistic-losses

Use this sub-skill when the user is choosing a point, quantile, distribution,
or robust loss, debugging quantile/level conversions, or matching a training
loss to prediction intervals or simulation outputs.

## What this route covers

- Point losses such as `MAE`, `MSE`, `RMSE`, `MAPE`, `SMAPE`, `MASE`, and
  `relMSE`.
- Quantile and probabilistic losses such as `MQLoss`, `IQLoss`,
  `DistributionLoss`, `PMM`, `GMM`, `NBMM`, and `sCRPS`.
- Robust losses such as `HuberLoss`, `TukeyLoss`, `HuberQLoss`,
  `HuberMQLoss`, `HuberIQLoss`, and `FreDF`.
- Level/quantile translation and prediction-interval alignment.

## What this route does not cover

- The panel dataframe contract.
- Choosing the model family.
- Auto*/distributed execution.
- Core fit/predict orchestration beyond what is needed to explain the loss.

If the user only needs to run a model after picking the loss, route to
`../core-forecasting/SKILL.md`. If the data layout is causing the failure, route
to `../data-and-exogenous/SKILL.md`.

## Read these bundled references

- `../../references/losses-reference.md` for the full loss-family overview.
- `../../references/api-reference.md` for the verified loss signatures.
- `references/troubleshooting.md` for quantile, compatibility, and mask errors.

## Run this bundled script

- `../../scripts/check_losses.py` for a small deterministic loss check.

## Common triggers

- "Which loss should I use for quantiles?"
- "How do I get prediction intervals?"
- "Why do duplicate quantiles warn?"
- "Why does valid_loss have to match the training loss?"
- "What does horizon_weight do?"

## Minimal route

1. Read `../../references/losses-reference.md`.
2. Use `../../scripts/check_losses.py` if you want a quick smoke of the loss
   surface.
3. Read `references/troubleshooting.md` when the loss configuration fails.

## Decision cues

- If the user already knows the loss and needs a model, route to
  `model-selection`.
- If the user needs the panel schema or future dataframe shape, route to
  `data-and-exogenous`.
- If the user needs the actual training run, route to `core-forecasting`.

## Safe default

When in doubt, start with `MAE` for a point forecast or `MQLoss(level=[80, 90])`
when the user explicitly wants quantiles.
