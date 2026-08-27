# Losses Reference

## Purpose

Read this when the user is choosing a training loss, validating a quantile or
prediction-interval setup, or debugging a probabilistic forecast.

## Loss families

### Point losses

- `MAE`, `MSE`, `RMSE`, `MAPE`, `SMAPE`, `MASE`, `relMSE`, `Accuracy`.
- These are the safest defaults when a user just wants a stable forecasting run.
- `MAE` is the common default in the quickstart and tiny smoke checks.

### Quantile and probabilistic losses

- `QuantileLoss`
- `MQLoss`
- `IQLoss`
- `HuberQLoss`, `HuberMQLoss`, `HuberIQLoss`
- `DistributionLoss`
- `PMM`, `GMM`, `NBMM`
- `sCRPS`

### Robust losses

- `HuberLoss`
- `TukeyLoss`
- `FreDF`

## Key compatibility rules

| Combination | Rule |
| --- | --- |
| `IQLoss` / `HuberIQLoss` | `valid_loss` must be the same family. |
| `MQLoss` / `HuberMQLoss` | `valid_loss` must be `MQLoss()` or `HuberMQLoss()`. |
| Point loss with distribution `valid_loss` | Not allowed. Use a point `valid_loss` such as `MAE` or `MSE`. |
| Distribution output with a different `valid_loss` | The model may coerce validation back to the training loss. |
| `relMSE`, `Accuracy`, `sCRPS` as training loss | Not allowed for training. |

## Quantiles and levels

- The API accepts either `level=[80, 90]` style coverage levels or explicit
  `quantiles=[...]`.
- Source tests show duplicate levels and duplicate quantiles are deduplicated
  with a warning.
- Helper functions like `level_to_quantiles`, `quantiles_to_level`, and
  `quantiles_to_outputs` are the conversion tools to remember.

## What the horizon weight does

`horizon_weight` reweights the loss across forecast steps. It is useful when
later horizons matter more than early ones, or when a custom objective wants a
specific temporal emphasis.

## Prediction intervals and simulation

- `PredictionIntervals(n_windows=2, method='conformal_distribution', step_size=1)`
  is the public interval helper.
- Conformal interval workflows depend on a fit-time validation window.
- Simulation helpers consume the fitted model state and the chosen loss family;
  route shape/data issues back to `core-forecasting` or `data-and-exogenous`.

## Small examples to remember

- `MAE(horizon_weight=...)` is the smallest safe loss smoke check.
- `MQLoss(level=[80, 90])` is the quickest way to validate quantile routing.
- `DistributionLoss(distribution='Normal', level=[80, 90])` is the simplest
  distribution-loss check.

## Read next

- `workflows.md` for prediction-interval and simulation examples.
- `troubleshooting.md` for quantile dedup, valid_loss, and masking failures.
