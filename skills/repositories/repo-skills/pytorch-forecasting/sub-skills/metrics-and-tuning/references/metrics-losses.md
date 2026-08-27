# Metrics and losses

This reference is for PyTorch Forecasting 1.8.0 metric and loss wiring. It is self-contained: use it with an installed `pytorch-forecasting` package and already-constructed datasets/dataloaders.

## Imports

```python
from pytorch_forecasting.metrics import (
    SMAPE,
    MAE,
    MAPE,
    RMSE,
    MASE,
    CrossEntropy,
    PoissonLoss,
    TweedieLoss,
    QuantileLoss,
    NormalDistributionLoss,
    NegativeBinomialDistributionLoss,
    LogNormalDistributionLoss,
    BetaDistributionLoss,
    MultivariateNormalDistributionLoss,
    ImplicitQuantileNetworkDistributionLoss,
    MQF2DistributionLoss,
    MultiLoss,
)
from pytorch_forecasting.metrics.base_metrics import AggregationMetric
```

`AggregationMetric` is available from `pytorch_forecasting.metrics.base_metrics`. `CompositeMetric` is created implicitly when metrics are added or scaled.

## Selection guide

| Target / objective | Use | Output size rule | Notes |
| --- | --- | --- | --- |
| General deterministic real-valued forecast | `MAE()` or `RMSE()` | `1` | `MAE` is robust and usually a safe default; `RMSE` punishes large errors and uses `reduction="sqrt-mean"` by default. |
| Relative-error reporting/training | `SMAPE()` or `MAPE()` | `1` | Intended for non-negative targets. `MAPE` is unstable near zero; `SMAPE` is bounded by denominator `abs(y_pred) + abs(y) + 1e-8`. |
| Scale-normalized deterministic error | `MASE()` | `1` | Needs encoder target history in `update()` so it can compute scaling from encoder+decoder target differences. |
| Classification over labels at each horizon | `CrossEntropy()` | number of classes | Prediction tensor is logits `[batch, horizon, n_classes]`; target is integer class ids `[batch, horizon]`. |
| Integer count target with log-rate output | `PoissonLoss()` | `1` | Applies `exp()` to the network output for predictions. Use a target normalizer that transforms the target into log-like space without applying the reverse transform twice. |
| Non-negative continuous/count-like target with Tweedie variance | `TweedieLoss(p=1.5)` | `1` | `p` must satisfy `1 <= p < 2`; applies `exp()` for predictions. Useful for zero-heavy positive amounts such as insurance-style losses. |
| Direct multi-quantile forecast | `QuantileLoss(quantiles=[...])` | `len(loss.quantiles)` | Default quantiles are `[0.02, 0.1, 0.25, 0.5, 0.75, 0.9, 0.98]`. Median/nearest-to-0.5 is used for point prediction. |
| Continuous probabilistic forecast | `NormalDistributionLoss()` | `len(loss.distribution_arguments)` = 2 | Model emits normalized distribution parameters; `transform_output()` appends target-scale information before scoring. |
| Overdispersed counts | `NegativeBinomialDistributionLoss()` | 2 | Requires a target normalizer that is not centered and not `log`/`logit`; `log1p` is handled specially. |
| Strictly positive skewed target | `LogNormalDistributionLoss(clamp_min=1e-12)` | 2 | Requires `log` or `log1p` target transformation. Actuals are clamped to positive support during loss. |
| Target constrained to `(0, 1)` | `BetaDistributionLoss()` | 2 | Requires `logit` transformation and centered target normalizer. Actuals are clipped away from 0 and 1. |
| Cross-sample multivariate normal dependence | `MultivariateNormalDistributionLoss(rank=10)` | `2 + rank` | Designed for DeepAR/DeepVAR-style multivariate forecasting. Not compatible with MPS accelerator in its distribution mapping. |
| Horizon-dependent multivariate quantile distribution | `MQF2DistributionLoss(prediction_length=H, hidden_size=4)` | `hidden_size` | Requires optional `cpflows`; output is special because `rescale_parameters()` flattens horizon parameters and `to_quantiles()` returns `[batch, prediction_length, n_quantiles]`. |
| Implicit quantile function | `ImplicitQuantileNetworkDistributionLoss(input_size=16)` | `input_size` | Uses a small neural quantile network and returns quantiles from sampled or requested quantile levels. |
| Multiple targets | `MultiLoss([loss_a, loss_b], weights=[...])` | list, one output size per target | `from_dataset()` can infer list output sizes for multi-target datasets; targets and predictions are lists in the same order. |
| Bias / add-up constraint | `base + AggregationMetric(metric=base_metric)` | same as base metric | Aggregates over the batch before scoring, so the numeric value depends on batch composition and batch size. |

Prefer `Model.from_dataset(dataset, loss=loss, ...)` when possible. The base model can infer `output_size` from `QuantileLoss`, `DistributionLoss`, label encoders, and `MultiLoss`; manual `output_size` is a common source of shape failures.

## Multi-horizon tensor contracts

PyTorch Forecasting metrics are built for multi-horizon forecasts, not just one-dimensional vectors.

- Point prediction tensor: `[batch, prediction_horizon]`.
- Extra output/channel tensor: `[batch, prediction_horizon, n_outputs]`.
- Target tensor: `[batch, prediction_horizon]`, or `(target, weight)`, or a packed sequence for variable decoder lengths.
- Most metric `forward()` calls reduce to a scalar by default. Set `reduction="none"` on `MultiHorizonMetric` subclasses to inspect per-sample/per-horizon losses.
- Valid reductions are `"mean"`, `"sqrt-mean"`, and `"none"`. `RMSE` defaults to `"sqrt-mean"`; most others default to `"mean"`.
- `MultiHorizonMetric.update()` masks padded decoder positions before reduction when lengths are known from packed sequences.

Example deterministic metric shape check:

```python
import torch
from pytorch_forecasting.metrics import SMAPE

y_pred = torch.rand(4, 6)       # [batch, horizon]
y = torch.rand(4, 6)            # [batch, horizon]
scalar = SMAPE()(y_pred, y)     # scalar tensor
matrix = SMAPE(reduction="none")(y_pred, y)  # [4, 6]
```

## Quantile loss shapes

`QuantileLoss` expects one output channel per requested quantile.

```python
import torch
from pytorch_forecasting.metrics import QuantileLoss

quantiles = [0.1, 0.5, 0.9]
loss = QuantileLoss(quantiles=quantiles)
y_pred = torch.rand(4, 6, len(quantiles))  # [batch, horizon, quantile]
y = torch.rand(4, 6)                       # [batch, horizon]

per_quantile = loss.loss(y_pred, y)        # [4, 6, 3]
scalar = loss(y_pred, y)                   # reduced scalar
point = loss.to_prediction(y_pred)         # [4, 6], median if present, nearest 0.5 otherwise
q = loss.to_quantiles(y_pred)              # [4, 6, 3]
```

For a `TemporalFusionTransformer` quantile model, keep these values aligned:

```python
loss = QuantileLoss(quantiles=[0.1, 0.5, 0.9])
model = TemporalFusionTransformer.from_dataset(
    training,
    loss=loss,
    output_size=len(loss.quantiles),  # optional if from_dataset can infer it
    learning_rate=0.03,
)
```

If the model was created with `output_size=7` but the loss has three quantiles, `QuantileLoss.loss()` will index the last dimension according to `loss.quantiles` and later layers may fail or silently optimize the wrong outputs.

## Point and count losses

### `SMAPE`, `MAE`, `MAPE`, `RMSE`

Use these for deterministic forecasts. They call `to_prediction()` before comparing to the target, so a `[batch, horizon, 1]` prediction can be squeezed to `[batch, horizon]` by the base metric. If a 3D point tensor has more than one last-dimension value and no quantile configuration, the base metric asserts that the extra dimension must be 1.

### `MASE`

`MASE` is different because it needs historical target values:

```python
metric = MASE()
metric.update(
    y_pred=decoder_prediction,          # [batch, decoder_horizon]
    target=decoder_target,              # [batch, decoder_horizon]
    encoder_target=encoder_target,      # [batch, encoder_length]
    encoder_lengths=encoder_lengths,    # [batch]
)
value = metric.compute()
```

At least two total target values across encoder+decoder are required. The scaling is `mean(abs(diff(concat(encoder_target, decoder_target)))) + 1e-6` per sample.

### `PoissonLoss` and `TweedieLoss`

Both interpret the network output in log space and apply `exp()` in `to_prediction()`.

```python
from pytorch_forecasting import EncoderNormalizer, TimeSeriesDataSet
from pytorch_forecasting.metrics import PoissonLoss

dataset = TimeSeriesDataSet(
    data,
    target="count",
    target_normalizer=EncoderNormalizer(
        transformation=dict(forward=torch.log1p)  # no reverse transform here
    ),
    # other dataset arguments ...
)
loss = PoissonLoss()
```

Use `PoissonLoss` for count data close to Poisson variance. Use `TweedieLoss(p=...)` for non-negative data where the variance scales as a power of the mean; `p` near 1 approaches Poisson-like behavior and near 2 approaches Gamma-like behavior.

## Classification loss

`CrossEntropy` is for discrete target classes per decoder step.

```python
from pytorch_forecasting.metrics import CrossEntropy

logits = torch.randn(batch_size, prediction_horizon, n_classes)
target = torch.randint(0, n_classes, (batch_size, prediction_horizon))
loss = CrossEntropy()
value = loss(logits, target)
labels = loss.to_prediction(logits)  # argmax labels, shape [batch, horizon]
```

Targets must be integer class ids; one-hot targets are not accepted by this loss implementation.

## Distribution losses

Distribution losses score parameterized probability distributions by negative log likelihood or a distribution-specific score. In ordinary model code, use `from_dataset(..., loss=loss)`: model `transform_output()` calls the loss's `rescale_parameters()` with the dataset target normalizer and target scale before the loss is evaluated.

### Univariate distributions

- `NormalDistributionLoss()` supports many target transformations. Raw model output size is 2; transformed prediction passed to `loss()` has target-scale fields plus `loc` and positive `scale`.
- `NegativeBinomialDistributionLoss()` is for overdispersed counts. It requires non-centered normalization and rejects `log`/`logit` transformations.
- `LogNormalDistributionLoss(clamp_min=1e-12)` requires `log` or `log1p` target transformation and clamps actuals to positive support.
- `BetaDistributionLoss()` requires a `logit` transformation and centered normalizer for bounded targets.

Manual shape probe for a normal prediction after the same kind of output transform a model applies:

```python
from pytorch_forecasting.data.encoders import TorchNormalizer

loss = NormalDistributionLoss()
normalizer = TorchNormalizer(transformation=None)
target_scale = torch.stack([
    torch.zeros(batch_size),  # target-scale center
    torch.ones(batch_size),   # target-scale scale
], dim=-1)
raw_params = torch.stack([
    torch.zeros(batch_size, horizon),  # normalized loc parameter
    torch.ones(batch_size, horizon),   # raw scale parameter; rescale_parameters applies softplus
], dim=-1)
params = loss.rescale_parameters(raw_params, target_scale=target_scale, encoder=normalizer)
y = torch.randn(batch_size, horizon)
per_step = loss.loss(params, y)       # [batch, horizon]
mean = loss.to_prediction(params)     # [batch, horizon]
quantiles = loss.to_quantiles(params) # [batch, horizon, len(loss.quantiles)]
```

### Multivariate and implicit quantile distributions

- `MultivariateNormalDistributionLoss(rank=...)` uses a low-rank multivariate normal and returns a scalar loss across the multivariate event. It asserts against MPS because the underlying PyTorch distribution path is not reliable there.
- `ImplicitQuantileNetworkDistributionLoss(input_size=..., hidden_size=..., n_loss_samples=...)` creates a neural quantile mapping. Raw output size is `input_size`; transformed prediction includes the raw parameters plus location and scale.
- `MQF2DistributionLoss(prediction_length=..., hidden_size=..., es_num_samples=...)` models a multivariate quantile function over the full prediction horizon. It requires `cpflows` and has a special flattened transformed-output contract. With `es_num_samples=None`, it uses maximum likelihood; otherwise it uses an energy score.

## Composite metrics

Metrics can be added and scaled to form a differentiable composite objective:

```python
from pytorch_forecasting.metrics import SMAPE, MAE

loss = SMAPE() + 1e-4 * MAE()
value = loss(y_pred, y)
```

The resulting `CompositeMetric` computes a weighted sum. `to_prediction()` and `to_quantiles()` delegate to the first metric, so put the primary output interpretation first.

## Aggregate/bias metric pattern

Use `AggregationMetric` when the objective should penalize mean bias across all samples in the batch:

```python
from pytorch_forecasting.metrics import MAE
from pytorch_forecasting.metrics.base_metrics import AggregationMetric

loss = MAE() + AggregationMetric(metric=MAE())
```

`AggregationMetric` calculates the metric on mean predictions and mean actuals across the batch dimension. Because errors can average out as batch size grows, this term changes with batch composition; keep batch size stable if comparing runs.

## Multi-target `MultiLoss`

For multiple targets, use one loss per target and optional weights:

```python
from pytorch_forecasting.metrics import MAE, QuantileLoss, MultiLoss

loss = MultiLoss(
    metrics=[MAE(), QuantileLoss(quantiles=[0.1, 0.5, 0.9])],
    weights=[1.0, 0.5],
)
model = SomeModel.from_dataset(training, loss=loss)
```

For multi-target datasets, `from_dataset()` can infer `output_size` as a list. If setting it manually, match the target order exactly, for example `[1, len(loss.metrics[1].quantiles)]`.

## Optional dependency notes

- Base installation covers standard point, quantile, and most distribution losses.
- `MQF2DistributionLoss` imports `cpflows` during initialization. Install the MQF2 extra before using it: `pip install "pytorch-forecasting[mqf2]"`.
- `optimize_hyperparameters()` requires `optuna`, `optuna-integration`, and `statsmodels`; install the tuning extra or those packages explicitly.
- `matplotlib` is optional for plotting LR finder curves. The finder result can still be used through `res.suggestion()` without plotting.

## Validate without training

Use the bundled helper from this sub-skill to check common shape contracts:

```bash
python scripts/check_metrics_shapes.py --case all
python scripts/check_metrics_shapes.py --case quantile --quantiles 0.1 0.5 0.9
python scripts/check_metrics_shapes.py --case optional
```
