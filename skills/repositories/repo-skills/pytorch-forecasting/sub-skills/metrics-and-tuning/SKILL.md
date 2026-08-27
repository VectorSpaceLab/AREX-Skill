---
name: metrics-and-tuning
description: "Choose and use PyTorch Forecasting metrics, losses, composite
  objectives, learning-rate finder setup, and Temporal Fusion Transformer Optuna
  tuning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Metrics and Tuning

Use this sub-skill when the task is to choose or wire PyTorch Forecasting metrics, loss functions, probabilistic output heads, composite or aggregate objectives, learning-rate finder settings, or Temporal Fusion Transformer Optuna tuning.

## Route here when

- Selecting among `SMAPE`, `MAE`, `MAPE`, `RMSE`, `MASE`, `CrossEntropy`, `PoissonLoss`, `TweedieLoss`, `QuantileLoss`, distribution losses, `MultiLoss`, or aggregate/composite objectives.
- Debugging tensor shapes for multi-horizon predictions, quantile outputs, distribution outputs, classification logits, or multi-target losses.
- Adding safe learning-rate finder or `optimize_hyperparameters()` recipes around already-built `TimeSeriesDataSet` dataloaders.
- Explaining base-install failures for MQF2 or Optuna tuning optional extras.

## Boundaries

- For full model construction, training loops, prediction calls, and architecture choice, use [`../forecasting-models/SKILL.md`](../forecasting-models/SKILL.md).
- For dataframe preparation, `TimeSeriesDataSet` construction, normalizers, dataloaders, and target-scale fields, use [`../data-pipeline/SKILL.md`](../data-pipeline/SKILL.md).
- This sub-skill may show small metric tensors and tuning wrappers, but it does not run training.

## Bundled references and tools

- [`references/metrics-losses.md`](references/metrics-losses.md) explains metric/loss selection, imports, API examples, multi-horizon and quantile tensor shapes, distribution-loss output sizing, optional dependencies, `MultiLoss`, and aggregate/bias objectives.
- [`references/tuning.md`](references/tuning.md) gives learning-rate finder and Temporal Fusion Transformer Optuna recipes, safe budgets, optional extras, generated artifacts, and failure modes.
- [`references/troubleshooting.md`](references/troubleshooting.md) maps common metric/tuning symptoms to causes and recovery steps, including non-finite loss, MQF2 `cpflows`, wrong `output_size`, aggregate metric batch effects, and LR finder stalls.
- [`scripts/check_metrics_shapes.py`](scripts/check_metrics_shapes.py) is a no-training argparse helper that constructs synthetic tensors and validates selected metric/loss shape contracts.

## Fast operating checklist

1. Confirm the task owner has already built a `TimeSeriesDataSet`/dataloader; if not, route to the data-pipeline sub-skill.
2. Choose the objective from the target semantics first: deterministic real value, quantiles, count target, classification label, bounded `(0, 1)` target, positive skewed target, multivariate/horizon-dependent target, or multi-target output.
3. Match model `output_size` to the loss. Prefer `Model.from_dataset(..., loss=loss)` so PyTorch Forecasting infers `output_size`; if manually setting it, use `len(QuantileLoss.quantiles)`, `1` for point losses, class count for `CrossEntropy`, or `len(loss.distribution_arguments)` for distribution losses.
4. Validate shape expectations with the bundled shape-check script before debugging a full training run.
5. Install optional extras only when needed: MQF2 requires `cpflows`; tuning requires `optuna`, `optuna-integration`, and `statsmodels`; plotting LR curves requires `matplotlib`.
