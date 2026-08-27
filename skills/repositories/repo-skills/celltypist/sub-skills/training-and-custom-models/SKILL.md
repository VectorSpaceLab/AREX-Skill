---
name: training-and-custom-models
description: "Plan and preflight custom CellTypist model training, including
  data preparation, SGD/mini-batch options, feature selection, downsampling, and
  model save/use handoff."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and Custom Models

Use this sub-skill when a task needs a custom CellTypist model trained from reference expression data, labels, and genes, or when training inputs must be validated before an expensive run.

## Start Here

1. Read [references/api-reference.md](references/api-reference.md) for the verified `celltypist.train` and `celltypist.samples.downsample_adata` signatures and parameter caveats.
2. Use [references/training-workflows.md](references/training-workflows.md) to choose one-pass logistic regression, SGD, mini-batch SGD, two-pass feature selection, sparse-safe settings, and model persistence.
3. Run [scripts/training_data_check.py](scripts/training_data_check.py) before expensive training when the user provides CSV/label/gene fixtures or asks why a run will fail.
4. Use [references/troubleshooting.md](references/troubleshooting.md) to map validation, solver, memory, GPU, mini-batch, feature-selection, and downsampling failures to concrete fixes.

## Boundaries and Routing

- Stay here for `celltypist.train`, `celltypist.samples.downsample_adata`, training matrix/label/gene validation, algorithm choice, feature-selection settings, sparse-memory safeguards, GPU caveats, and writing a trained model.
- Route inference with a trained model to `../annotation-workflows/`.
- Route model conversion, subsetting, built-in model discovery, or model metadata management to `../model-management/`.
- Route final dotplots, result tables, and visualization polish to `../visualization-and-results/`.

## Fast Decision Rules

- Use default logistic regression for small or intermediate references when calibrated probabilities matter and runtime is acceptable.
- Use `use_SGD=True` for large matrices where runtime is the bottleneck, accepting that probability calibration may need more tuning.
- Use `use_SGD=True, mini_batch=True` only when the reference has more cells than `batch_size`; consider `balance_cell_type=True` for rare labels.
- Use `with_mean=False` for sparse input to avoid densifying during scaling; consider `check_expression=False` only when the user intentionally trains on an HVG/subset matrix that cannot pass whole-transcriptome normalization checks.
- Use `feature_selection=True` only when the number of genes is greater than `top_genes` and the extra first-pass SGD cost is justified.
