# Losses and Metrics

This reference summarizes SMP loss and metric APIs needed for training/evaluation loops. Use it with the validator in [scripts/validate_training_shapes.py](../scripts/validate_training_shapes.py) when debugging tensor mode combinations.

## Mode Constants

SMP exposes these string constants in `smp.losses`:

| Constant | Value | Use case | Logit shape | Target shape |
| --- | --- | --- | --- | --- |
| `BINARY_MODE` | `"binary"` | One foreground class against background | `(N, 1, H, W)` | Loss: `(N, H, W)` or `(N, 1, H, W)`; metrics: prefer `(N, 1, H, W)` |
| `MULTICLASS_MODE` | `"multiclass"` | Mutually exclusive classes | `(N, C, H, W)` | `(N, H, W)` integer ids in `0..C-1` |
| `MULTILABEL_MODE` | `"multilabel"` | Independent overlapping labels | `(N, C, H, W)` | `(N, C, H, W)` binary channels |

Use `smp.losses.BINARY_MODE`, `smp.losses.MULTICLASS_MODE`, and `smp.losses.MULTILABEL_MODE` instead of spelling strings by hand when possible.

## Loss Selection

| Loss | Modes | Inputs | Important options |
| --- | --- | --- | --- |
| `DiceLoss(mode, ...)` | binary, multiclass, multilabel | Overlap loss; accepts logits by default | `classes`, `log_loss`, `from_logits`, `smooth`, `ignore_index`, `class_weights` for multiclass/multilabel only |
| `JaccardLoss(mode, ...)` | binary, multiclass, multilabel | IoU/Jaccard loss; accepts logits by default | Same shape behavior as Dice; empty target channels contribute zero |
| `TverskyLoss(mode, ...)` | binary, multiclass, multilabel | Dice-like loss with asymmetric FP/FN penalties | `alpha` penalizes false positives, `beta` penalizes false negatives, `gamma` powers aggregate loss |
| `FocalLoss(mode, ...)` | binary, multiclass, multilabel | Hard-example loss | `alpha`, `gamma`, `ignore_index`, `from_logits`, `reduction`, `normalized`, `reduced_threshold`, `class_weights` for multiclass/multilabel only |
| `LovaszLoss(mode, ...)` | binary, multiclass, multilabel | Direct IoU-surrogate style loss | Use logits-like scores; multiclass branch applies softmax internally; supports `per_image` and `ignore_index` |
| `SoftBCEWithLogitsLoss(...)` | binary, multilabel | BCE-with-logits with optional label smoothing | Use logits, not sigmoid probabilities; target should match binary/multilabel shape; supports `ignore_index`, `smooth_factor`, `pos_weight` |
| `SoftCrossEntropyLoss(...)` | multiclass | Cross-entropy with optional label smoothing | Use logits `(N, C, H, W)` and long target `(N, H, W)`; supports `ignore_index`, `smooth_factor`, `dim`; set `smooth_factor=0.0` explicitly for smoke checks if the installed version does not handle `None` |
| `MCCLoss(eps=...)` | binary only | Matthews correlation coefficient loss | Expects probability-like or hard binary predictions; apply `torch.sigmoid(logits)` yourself if model emits logits |

Default to `DiceLoss` or `JaccardLoss` for segmentation overlap, add `SoftBCEWithLogitsLoss` or `SoftCrossEntropyLoss` when dense per-pixel classification stability is needed, and use `FocalLoss`/`TverskyLoss` for imbalance-sensitive cases.

## Constructor Signatures

Installed SMP exposes these loss signatures:

```python
smp.losses.DiceLoss(mode, classes=None, log_loss=False, from_logits=True, smooth=0.0, ignore_index=None, eps=1e-7, class_weights=None)
smp.losses.JaccardLoss(mode, classes=None, log_loss=False, from_logits=True, smooth=0.0, ignore_index=None, eps=1e-7, class_weights=None)
smp.losses.TverskyLoss(mode, classes=None, log_loss=False, from_logits=True, smooth=0.0, ignore_index=None, eps=1e-7, alpha=0.5, beta=0.5, gamma=1.0, class_weights=None)
smp.losses.FocalLoss(mode, alpha=None, gamma=2.0, ignore_index=None, from_logits=True, eps=1e-7, reduction="mean", normalized=False, reduced_threshold=None, class_weights=None)
smp.losses.LovaszLoss(mode, per_image=False, ignore_index=None, from_logits=True)
smp.losses.SoftBCEWithLogitsLoss(weight=None, ignore_index=-100, reduction="mean", smooth_factor=None, pos_weight=None)
smp.losses.SoftCrossEntropyLoss(reduction="mean", smooth_factor=None, ignore_index=-100, dim=1)
smp.losses.MCCLoss(eps=1e-5)
```

## `from_logits` Rules

- SMP models normally return raw logits when created with `activation=None`; keep `from_logits=True` for `DiceLoss`, `JaccardLoss`, `TverskyLoss`, and `FocalLoss`.
- If a model has an activation configured or your code applies `sigmoid`/`softmax` before the loss, set `from_logits=False` for losses that support it.
- Do not pass sigmoid probabilities to `SoftBCEWithLogitsLoss` or softmax probabilities to `SoftCrossEntropyLoss`; both expect logits.
- For `MCCLoss`, pass probabilities or hard binary predictions; it does not apply sigmoid internally.

## Metric Flow

SMP metrics use a two-step API:

```python
tp, fp, fn, tn = smp.metrics.get_stats(output, target, mode=mode, threshold=threshold, num_classes=num_classes)
iou = smp.metrics.iou_score(tp, fp, fn, tn, reduction="micro", zero_division=1.0)
f1 = smp.metrics.f1_score(tp, fp, fn, tn, reduction="micro", zero_division=1.0)
```

`get_stats` expects `output` and `target` to have identical shapes. It returns true-positive, false-positive, false-negative, and true-negative tensors of shape `(N, C)`.

| Mode | Metric output input | Required metric args | Notes |
| --- | --- | --- | --- |
| Binary | Integer mask `(N, 1, H, W)` or float scores of same shape | `mode="binary"`; add `threshold=0.5` for float scores | If you squeeze to `(N, H, W)`, avoid classwise interpretation; unsqueeze for clarity |
| Multiclass | Integer class ids `(N, H, W)` from `logits.argmax(dim=1)` | `mode="multiclass", num_classes=C` | Do not pass logits, probabilities, or `threshold` |
| Multilabel | Integer mask `(N, C, H, W)` or float scores of same shape | `mode="multilabel"`; add `threshold=0.5` for float scores | Apply sigmoid before thresholding if using logits |

## Reductions

Metric functions such as `iou_score`, `f1_score`, `accuracy`, `precision`, and `recall` accept these reductions:

- `"micro"`: sum statistics over images/classes, then compute one score.
- `"macro"`: compute per-class scores after summing over images, then average.
- `"weighted"`: like macro, but requires `class_weights`.
- `"micro-imagewise"`: compute one score per image from summed classes, then average images.
- `"macro-imagewise"`: compute per-image, per-class scores and average.
- `"weighted-imagewise"`: imagewise weighted average; requires `class_weights`.
- `"none"` or `None`: return per-image/per-class scores.

Use `zero_division=1.0`, `0.0`, or `"warn"` to control all-negative or empty-mask cases.

## Class Weights

- `class_weights` are supported by `DiceLoss`, `JaccardLoss`, `TverskyLoss`, and `FocalLoss` only for multiclass and multilabel modes.
- Binary mode rejects `class_weights` for these losses; use `pos_weight` in `SoftBCEWithLogitsLoss` for binary imbalance.
- Weight lists should have one value per output class/channel, even if only a subset of classes contributes.
- Scaling all class weights by the same constant does not change the normalized weighted loss.

## Ignore Index

- Losses commonly accept `ignore_index` and mask ignored pixels out of loss computation.
- `smp.metrics.get_stats` supports `ignore_index` only for `mode="multiclass"` and requires it to be outside the valid class id range, such as `-1` or `255`.
- For binary or multilabel metrics with ignored pixels, filter or mask predictions/targets before calling `get_stats`; do not pass `ignore_index` directly.
