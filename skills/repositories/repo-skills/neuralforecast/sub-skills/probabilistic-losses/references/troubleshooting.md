# Probabilistic Losses Troubleshooting

## Purpose

Read this when a quantile, distribution, or robust-loss workflow fails or when
prediction intervals do not line up with the chosen loss.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Duplicate quantile or level warning | The configuration repeated a value. | Remove duplicates or accept the warning if it is harmless. |
| `valid_loss` compatibility error | The training and validation losses are from incompatible families. | Use the matching loss family. |
| Distribution loss with point validation | The validation loss is not compatible with a distribution output. | Switch to a point validation loss. |
| Horizon-weight error | The provided weight vector does not match the horizon. | Make the weight vector length equal the forecast horizon. |
| Masking issue in a loss test | The mask or sample-weight column is malformed. | Clean the input data and rerun the data validator. |
| Interval columns missing | The model was not fit with compatible prediction-interval settings. | Fit with `PredictionIntervals(...)` and the right validation window. |

## Next checks

1. Run `../../scripts/check_losses.py`.
2. If the problem is really about the panel shape, route back to `data-and-exogenous`.
3. If the problem is about the training loop after the loss is chosen, route to `core-forecasting`.

## When to stop

If the user needs a different model family to support the chosen loss or
interval method, route to `model-selection`.
