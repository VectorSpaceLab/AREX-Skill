# Engine, metrics, preprocessing, post-processing, visualization

This reference covers the core Anomalib training and evaluation loop without CLI parsing, export internals, or pipeline orchestration.

## Core execution model

`Engine` is a thin wrapper around PyTorch Lightning's `Trainer` with Anomalib-specific workspace setup and callback wiring.

Common entry points:

- `Engine.fit(model, ...)` trains and, for zero-/few-shot models, validates instead of fitting.
- `Engine.train(model, ...)` runs `fit` and then `test`.
- `Engine.validate(model, ...)` runs validation only.
- `Engine.test(model, ...)` runs validation first when the model needs threshold/normalization state.
- `Engine.predict(model, ...)` may also validate first for zero-/few-shot models when `ckpt_path` is not provided.
- `Engine.from_config(config_path, **overrides)` returns `(engine, model, datamodule)` for config-driven startup.

Workspace layout:

- `fit` uses a versioned directory.
- `test` and `predict` resolve to the latest run directory.
- The path is derived from `default_root_dir / model.name / dataset_name / category`.

Default checkpointing:

- When `barebones=False` and no `ModelCheckpoint` is already present, `Engine` inserts a default checkpoint callback under `weights/lightning/model.ckpt`.
- `Engine.best_model_path` exposes the selected checkpoint path.
- `barebones=True` skips that default auto-inserted checkpoint callback.

## Training modes

### Standard mode

Use standard mode when you want the usual Lightning experience:

- checkpointing
- logging
- progress bar
- model summary

### Barebones mode

Use `barebones=True` for a lightweight CPU smoke or performance-overhead investigation.

Important differences:

- Lightning logging is disabled.
- The default auto-inserted checkpoint callback is skipped.
- Progress bar and model summary overhead are removed.
- Sanity checking is disabled.
- `LightningModule.log(...)` is disabled.

Anomalib's `Evaluator` compensates for this by writing computed metrics directly into `trainer.callback_metrics` and `trainer.logged_metrics` when needed, so `Engine.test()` can still return metrics in barebones mode when the evaluator callback is present.

### Zero-shot and few-shot guidance

For zero-shot and few-shot models:

- `Engine.fit()` runs validation only, because the model mainly needs normalization and thresholding state.
- `Engine.test()` and `Engine.predict()` may validate first if `ckpt_path` is not provided.

If validation never runs, post-processing thresholds and normalization buffers may stay unset.

## Metrics

### AnomalibMetric basics

`AnomalibMetric` extends TorchMetrics with batch-field binding.

Key arguments:

- `fields`: batch fields to extract
- `prefix`: prepend to the metric name
- `strict`: if `True`, missing fields raise; if `False`, missing fields are skipped and `compute()` can return `None`

Two frequent naming rules:

1. Use the right field names from Anomalib dataclasses.
2. Prefix metrics of the same class to avoid Lightning name collisions.

Example:

```python
from anomalib.metrics import F1Score

image_f1 = F1Score(fields=["pred_label", "gt_label"], prefix="image_")
pixel_f1 = F1Score(fields=["pred_mask", "gt_mask"], prefix="pixel_")
```

Without prefixes, both metrics would be named `F1Score`.

### Default evaluator metrics

The default evaluator created by `AnomalibModule.configure_evaluator()` uses these metrics:

| Name | Fields | Notes |
| --- | --- | --- |
| `image_AUROC` | `pred_score`, `gt_label` | Image-level ranking metric |
| `image_F1Score` | `pred_label`, `gt_label` | Image-level thresholded classification |
| `pixel_AUROC` | `anomaly_map`, `gt_mask` | Uses `strict=False` so missing masks do not hard fail |
| `pixel_F1Score` | `pred_mask`, `gt_mask` | Uses `strict=False` for the same reason |

That default evaluator is a good baseline for most anomaly detection models.

### Stage-specific metric choice

Validation metrics should usually be threshold-search or ranking metrics:

- `AUROC`
- `AUPR`
- `F1Max`
- `F1AdaptiveThreshold`

Test metrics can include thresholded metrics and localization metrics:

- `F1Score`
- `AUROC`
- `PRO`
- `AUPRO`
- `PIMO` / `AUPIMO`
- `PGn` / `PBn`

### Threshold helpers

`PostProcessor` relies on two stateful metric helpers:

- `F1AdaptiveThreshold` for image/pixel thresholds
- `MinMax` for normalization ranges

These helpers need validation evidence. If the validation set has only normal or only anomalous samples, `F1AdaptiveThreshold` warns and falls back to an extreme observed score.

### Device behavior

`Evaluator` computes metrics on CPU by default when only one device is used.

- `compute_on_cpu=True` is the default.
- On multi-device runs, it is automatically treated as `False`.

GPU-only metric/device checks such as PRO consistency are optional and should not block CPU work.

## Pre-processing

`PreProcessor` is both a `torch.nn.Module` and a Lightning callback.

Behavior:

- `on_train_batch_start`, `on_validation_batch_start`, `on_test_batch_start`, and `on_predict_batch_start` transform `batch.image` and `batch.gt_mask` in place.
- `forward()` is export-time behavior and expects a tensor input.

Shape guidance:

- image batches should generally be `(B, C, H, W)`
- masks should generally be `(B, H, W)`

If a transform fails, the issue is usually one of:

- transform does not accept the paired `(image, mask)` signature
- image and mask shapes are not aligned
- the transform was only designed for export-time tensor inputs

A safe CPU-only example is to use torchvision v2 transforms such as `Resize`, `ToImage`, and `ToDtype`.

## Post-processing

`PostProcessor` is both a module and a callback.

What it does:

- collects thresholds and min/max statistics during validation
- normalizes `pred_score` and `anomaly_map`
- converts scores to `pred_label` and `pred_mask` during test/predict

Important behavior:

- It needs at least one of `pred_score` or `anomaly_map`.
- If neither is provided, it raises `ValueError`.
- If a threshold buffer is still `NaN`, thresholding can no-op and leave raw predictions untouched.
- `enable_threshold_matching=True` lets one threshold stand in for the other when only one side is available.

`MEBinPostProcessor` is the precision-oriented alternative:

- it computes per-image masks using connected-component stability
- it can be better for downstream classification or anomaly discovery
- it may lower pixel F1 compared with the default global thresholding path

`OneClassPostProcessor` in `src/anomalib/post_processing/one_class.py` is the one-class specialization described in the docs.

## Visualization

`ImageVisualizer` is the main callback for image visualization.

Accepted inputs:

- `ImageItem`
- `NumpyImageItem`
- `ImageBatch`
- `NumpyImageBatch`

Behavior:

- single items and single-item batches return a single `PIL.Image.Image`
- multi-item batches return a list of images
- when `output_dir` is not set, the callback saves to `trainer.default_root_dir / "images"`
- `visualize_image_item(...)` returns `None` when required fields are missing

The visualization module is marked experimental in the docs, so keep usage conservative and prefer small, explicit field lists.

## Config-driven startup

`Engine.from_config(config_path, **overrides)` is the fastest config-based training entry point.

It returns:

1. a configured `Engine`
2. a configured `AnomalibModule`
3. a configured `AnomalibDataModule`

Use dotted overrides such as `data.train_batch_size=8` when you need a small config tweak without editing the YAML file.
