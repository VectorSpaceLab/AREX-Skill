# Metrics and tuning troubleshooting

Use this table when a metric, loss, or tuning call fails before investigating a full model training loop.

## Non-finite, NaN, or infinite loss

**Symptoms**

- Warning: `Loss is not finite. Resetting it to 1e9`.
- Assertion: `Loss should not be nan` or `Loss should not be infinite`.
- Validation loss is `nan`, `inf`, or immediately explodes during LR finding.

**Likely causes**

- Loss support does not match target values: `LogNormalDistributionLoss` received zero/negative actuals before clamping, `BetaDistributionLoss` received values outside `(0, 1)`, or count losses received negative targets.
- Target normalizer does not match the distribution loss. Examples: `NegativeBinomialDistributionLoss` with centered normalization or `log`/`logit`; `BetaDistributionLoss` without a centered `logit` transform; `LogNormalDistributionLoss` without `log`/`log1p` transform.
- `PoissonLoss` or `TweedieLoss` is used without log-space target handling, so `exp()` creates huge predictions.
- LR finder range is too wide or model gradients explode before enough finite points are collected.
- `MAPE` target values are near zero, causing extreme percentage errors.

**Recovery**

1. Run the bundled shape helper for the selected loss to rule out tensor-rank mistakes.
2. Verify target domain: counts are non-negative integers, beta targets are strictly inside `(0, 1)`, log-normal targets are positive, classification targets are integer class ids.
3. Rebuild the `TimeSeriesDataSet` with a normalizer compatible with the selected loss, or switch to a deterministic loss such as `MAE()` while debugging.
4. For `PoissonLoss`/`TweedieLoss`, use a log-like forward transform without double reverse transformation.
5. Lower `max_lr`, set `gradient_clip_val`, and test a very small training budget before running Optuna.

## MQF2 fails on a base install

**Symptoms**

- `ModuleNotFoundError: No module named 'cpflows'`.
- Failure occurs when constructing `MQF2DistributionLoss(...)`, before training starts.

**Cause**

`MQF2DistributionLoss` imports `cpflows` during initialization. The base package does not install that optional dependency.

**Recovery**

- Install the optional extra before using MQF2: `pip install "pytorch-forecasting[mqf2]"`.
- If optional installs are not allowed, use `QuantileLoss`, `ImplicitQuantileNetworkDistributionLoss`, `NormalDistributionLoss`, or another base-install loss instead.
- Keep `prediction_length` equal to the decoder prediction length used by the dataset/model.

## Optuna tuning fails on a base install

**Symptoms**

- `ImportError` from `optimize_hyperparameters()` mentioning `optuna`, `statsmodels`, or Optuna integration.
- `ModuleNotFoundError: No module named 'optuna'` or missing `optuna.integration` callback.

**Cause**

The tuning stack is optional. `optimize_hyperparameters()` needs `optuna`, `optuna-integration`, and `statsmodels`.

**Recovery**

```bash
pip install "pytorch-forecasting[tuning]"
# or
pip install "optuna>=3.1,<5" optuna-integration statsmodels
```

Then run a smoke search first: `n_trials=1`, `max_epochs=1`, short `timeout`, and small train/validation batch limits.

## Wrong `output_size` vs quantiles or distribution arguments

**Symptoms**

- Quantile loss indexes beyond the prediction tensor's last dimension.
- Model head output has `[batch, horizon, 1]` but `QuantileLoss` expects 7 quantiles.
- `CrossEntropy` receives logits with the wrong class count or target rank.
- Multi-target model returns a tensor where `MultiLoss` expects a list, or output-size list order does not match target order.

**Cause**

The last prediction dimension does not match the selected loss.

**Recovery**

- Prefer `Model.from_dataset(training, loss=loss)` and omit `output_size` unless you must override it.
- For `QuantileLoss`, set `output_size=len(loss.quantiles)`.
- For deterministic point losses, set `output_size=1`.
- For `CrossEntropy`, set `output_size=n_classes` and use integer class targets `[batch, horizon]`.
- For distribution losses, set `output_size=len(loss.distribution_arguments)`; for `MultivariateNormalDistributionLoss(rank=r)`, that is `2 + r`; for `ImplicitQuantileNetworkDistributionLoss(input_size=s)`, that is `s`; for `MQF2DistributionLoss(hidden_size=h)`, that is `h`.
- For `MultiLoss`, set `output_size` to a list in target order, for example `[1, len(quantile_loss.quantiles)]`.

## Aggregate/bias metric changes with batch size

**Symptoms**

- `MAE() + AggregationMetric(MAE())` gives different values when only batch size changes.
- Aggregate loss seems smaller for larger batches.

**Cause**

`AggregationMetric` first averages predictions and targets across samples in the current batch, then applies the wrapped metric. Errors can cancel as batch size grows; batch composition affects the aggregate term.

**Recovery**

- Use aggregate metrics only when add-up or bias reduction is the intended objective.
- Keep batch size and batch sampling stable across comparable experiments.
- Log the base metric separately from the aggregate term so you can see whether aggregate improvements hide point-error regressions.
- Avoid aggregate terms for tiny or highly heterogeneous batches unless that batch-level behavior is desired.

## LR finder does not finish

**Symptoms**

- LR finder stops early, returns no suggestion, or has too few finite points.
- Training appears to freeze during `lr_find`.
- FAQ-like symptom: CPU/GPU activity is high but no useful LR result appears.

**Likely causes**

- `fast_dev_run=True` is enabled.
- An artificial very small `limit_train_batches` prevents enough LR steps.
- No target normalizer or a target normalizer incompatible with the selected loss.
- `early_stop_threshold` too low for the loss scale.
- `max_lr` too high, causing loss explosion.
- Plot logging is enabled without a logger or without `matplotlib`.

**Recovery**

1. Disable `fast_dev_run`.
2. Remove tiny train-batch limits, or use full-epoch semantics for the finder.
3. Set model `log_interval=-1` and `log_val_interval=-1` during LR finding.
4. Use `min_lr=1e-5`, a conservative `max_lr` such as `0.1` or `0.3`, and a larger `early_stop_threshold` such as `1000.0` or `10000.0`.
5. Ensure the dataset target normalizer matches the selected loss.
6. Use `res.suggestion()` without plotting, or install `matplotlib` before `res.plot(...)`.

## CrossEntropy shape or dtype errors

**Symptoms**

- `expected scalar type Long` or similar dtype error.
- Loss reshape errors around class dimension.
- Predictions are probabilities or one-hot targets rather than logits and class ids.

**Cause**

`CrossEntropy` wraps `torch.nn.functional.cross_entropy` over flattened `[batch*horizon, n_classes]` logits and `[batch*horizon]` integer targets.

**Recovery**

- Pass raw logits shaped `[batch, horizon, n_classes]`.
- Pass target class ids shaped `[batch, horizon]` with integer dtype.
- Do not apply softmax before the loss.

## MASE requires encoder history

**Symptoms**

- Calling `MASE()(y_pred, y)` fails or produces an unusable value.
- Assertion: at least two target values are needed to calculate scaling.

**Cause**

`MASE` needs encoder targets and encoder lengths to compute the scale from historical target differences.

**Recovery**

Call `update()` with `encoder_target` and `encoder_lengths`, or use `MAE`/`RMSE` if no historical target values are available.

## Multivariate distribution special cases

**Symptoms**

- `MultivariateNormalDistributionLoss` fails on MPS.
- Loss output is scalar rather than `[batch, horizon]`.
- MQF2 quantiles have a different internal shape than ordinary `DistributionLoss` quantiles.

**Cause**

Multivariate losses operate over an event dimension rather than independent per-horizon univariate outputs. The multivariate normal implementation explicitly rejects MPS; MQF2 flattens horizon parameters after output transformation.

**Recovery**

- Use CPU or CUDA for `MultivariateNormalDistributionLoss`.
- Do not assume every distribution loss returns per-horizon loss tensors.
- For MQF2, set `prediction_length` to the decoder horizon and test `to_quantiles()` shape `[batch, prediction_length, n_quantiles]` before training.
