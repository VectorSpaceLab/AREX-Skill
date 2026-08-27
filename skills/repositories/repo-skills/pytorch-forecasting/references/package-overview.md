# PyTorch Forecasting Package Overview

## When to read

Read this for a quick map of PyTorch Forecasting 1.8.0 capabilities, public API
families, optional extras, and the v1/v2 split before selecting a sub-skill.

## Package identity

- Distribution: `pytorch-forecasting`
- Import module: `pytorch_forecasting`
- Purpose: high-level deep-learning time-series forecasting with PyTorch and
  Lightning, including data containers, normalizers, metrics/losses, model
  architectures, and tuning helpers.
- Supported Python from metadata: `>=3.10,<3.15`
- Core runtime dependencies: `torch`, `lightning`, `numpy`, `pandas`, `scipy`,
  `scikit-learn`, and `scikit-base`.

Minimal import check:

```python
import pytorch_forecasting as pf
from pytorch_forecasting import TimeSeriesDataSet, TemporalFusionTransformer, QuantileLoss
print(pf.__version__)
```

## Stable v1 user path

Use the stable v1 path for production or ordinary package-use tasks:

1. Prepare a pandas DataFrame with integer `time_idx`, target column(s), and
   one or more `group_ids`.
2. Build a `TimeSeriesDataSet` with covariate roles, encoder/prediction lengths,
   target normalizer, encoders/scalers, and missing-timestep policy.
3. Create validation/test/prediction datasets with
   `TimeSeriesDataSet.from_dataset()` so normalizers and encoders remain aligned.
4. Convert datasets to dataloaders with `to_dataloader()`.
5. Choose a v1 model and instantiate it with `ModelClass.from_dataset(training,
   ...)`.
6. Train with `lightning.pytorch.Trainer`, predict with `model.predict()`, and
   inspect or plot outputs when optional plotting/logging dependencies exist.

Public v1 model families include `Baseline`, `TemporalFusionTransformer`,
`NBeats`, `NBeatsKAN`, `NHiTS`, `DeepAR`, `RecurrentNetwork`, `DecoderMLP`,
`TiDEModel`, `TimeXer`, and `xLSTMTime`.

## Experimental API-v2 path

API-v2 is beta/WIP in this source snapshot. Use it only when the user explicitly
asks for v2 or is experimenting with the new layered architecture:

- D1 layer: `TimeSeries` ingests raw tabular data and exposes metadata.
- D2 layer: `EncoderDecoderTimeSeriesDataModule` or `TslibDataModule` prepares
  dataloaders and model metadata.
- M layer: direct Lightning models such as v2 `TFT`, `DLinear`, `Samformer`,
  `TimeXer`, `DecoderMLP_v2`, and `SOFTS`.
- P/package layer: wrappers such as `TFT_pkg_v2` that accept `datamodule_cfg`,
  `model_cfg`, and `trainer_cfg`, then expose `fit()` and `predict()`.

Do not present v2 as the production default unless a refreshed provenance file
shows that this status changed.

## Metrics and losses

PyTorch Forecasting metrics are multi-horizon aware. Common point metrics and
losses include `SMAPE`, `MAE`, `MAPE`, `RMSE`, `MASE`, `CrossEntropy`,
`PoissonLoss`, and `TweedieLoss`. `QuantileLoss` supports non-parametric
uncertainty estimates with a default quantile list. Distribution losses include
`NormalDistributionLoss`, `NegativeBinomialDistributionLoss`,
`LogNormalDistributionLoss`, `BetaDistributionLoss`,
`MultivariateNormalDistributionLoss`, `ImplicitQuantileNetworkDistributionLoss`,
and `MQF2DistributionLoss`.

Use `MultiLoss` or metric addition for composite objectives. Ensure model
`output_size` agrees with the selected loss, especially for quantiles,
distributions, or multi-target output.

## Optional extras

| Extra or dependency | Enables | Notes |
| --- | --- | --- |
| `pytorch-forecasting[tuning]` | Optuna-based tuning helpers and related dependencies | Use for `optimize_hyperparameters()` and tuning workflows; still set small budgets first. |
| `pytorch-forecasting[mqf2]` | `MQF2DistributionLoss` runtime dependency `cpflows` | A base install can import the class but instantiation/use can fail without `cpflows`. |
| `matplotlib` | Plotting/interpretation helpers | Optional; plotting guidance should degrade gracefully when absent. |
| `tensorboard` or `tensorboardX` | TensorBoard logging | Lightning may fall back to CSV logging if TensorBoard packages are absent. |
| CUDA-enabled `torch` | GPU acceleration | Not required for the selected CPU skill scope; do not claim GPU verification unless the runtime environment proves it. |

## Sub-skill routing summary

- Use `data-pipeline` for tabular data contracts, `TimeSeriesDataSet`, encoders,
  normalizers, dataloaders, and CSV validation.
- Use `forecasting-models` for v1 model selection, `.from_dataset()`, Lightning
  training, checkpointing, prediction, and interpretation.
- Use `metrics-and-tuning` for metric/loss selection, tensor shapes,
  probabilistic heads, learning-rate finder setup, and Optuna tuning.
- Use `api-v2-workflows` for beta v2 D1/D2/M/P-layer workflows.
- Use `custom-components` for custom metrics/models/package wrappers and focused
  maintainer-style tests.
