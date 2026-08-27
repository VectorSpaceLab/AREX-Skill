# Troubleshooting Training and Evaluation

Use this guide when SMP losses or metrics fail on shapes, modes, thresholds, or ignored pixels. The validator in [scripts/validate_training_shapes.py](../scripts/validate_training_shapes.py) can reproduce safe tiny combinations.

## Shape and Mode Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Binary loss receives logits shaped `(N, C, H, W)` with `C > 1` | Using `BINARY_MODE` for a multiclass head | Use `classes=1` with `BINARY_MODE`, or switch to `MULTICLASS_MODE` with target `(N, H, W)` |
| Multiclass loss fails in `one_hot` or class ids are out of range | Target contains values outside `0..C-1` or ignored label is not configured | Clean/remap target ids and pass `ignore_index` for void labels |
| Multilabel loss complains about reshape or channel mismatch | Target is `(N, H, W)` class ids instead of `(N, C, H, W)` binary channels | Convert each label to its own channel or use `MULTICLASS_MODE` |
| `get_stats` says output shape is not target shape | Metrics require identical output/target shapes after post-processing | For binary/multilabel, pass `(N, C, H, W)` masks; for multiclass, pass `(N, H, W)` class ids |
| Metrics reject float output without threshold | Float probabilities were passed to `get_stats` with `threshold=None` | Pass `threshold=0.5`, or convert predictions to integer masks before `get_stats` |

## Missing Channel Dimension

Binary datasets often return masks as `(N, H, W)`. Most SMP overlap losses can reshape that target, but metrics are clearer and safer with `(N, 1, H, W)`.

```python
if masks.ndim == 3:
    masks = masks.unsqueeze(1)
```

Do not unsqueeze multiclass masks for `SoftCrossEntropyLoss` or multiclass `DiceLoss`; multiclass targets should stay `(N, H, W)`.

## `from_logits` Misuse

- Raw SMP model output with `activation=None`: use `from_logits=True` for Dice/Jaccard/Tversky/Focal.
- Model output after `sigmoid` or `softmax`: use `from_logits=False` for Dice/Jaccard/Tversky/Focal.
- `SoftBCEWithLogitsLoss` and `SoftCrossEntropyLoss` always expect logits.
- `MCCLoss` does not apply sigmoid; pass `torch.sigmoid(logits)` or hard binary masks.

A common bug is applying `sigmoid` in the model and also using `from_logits=True`, which effectively applies activation twice inside overlap losses.

## Class Weights

- `class_weights` are not supported in binary mode for Dice/Jaccard/Tversky/Focal; use `pos_weight` in `SoftBCEWithLogitsLoss` for binary imbalance.
- For multiclass and multilabel, provide exactly one weight per class/channel.
- Weighted metric reductions such as `"weighted"` and `"weighted-imagewise"` require `class_weights`.
- Uniform weights should match unweighted behavior; if not, verify class/channel ordering.

## Ignore Index

- Losses can usually receive ignored labels via `ignore_index`.
- Multiclass metrics support `ignore_index`, but it must be outside the valid class id range, for example `-1` or `255` when classes are `0..C-1`.
- Binary and multilabel `smp.metrics.get_stats` do not support `ignore_index`; mask ignored pixels before metrics or skip those pixels by custom filtering.
- For multilabel ignored pixels, prefer losses with elementwise masking behavior such as Dice/Jaccard/Tversky or `SoftBCEWithLogitsLoss`; verify `FocalLoss(mode="multilabel", ignore_index=...)` on a tiny batch before using it in a real loop.
- Do not use `ignore_index=0` for multiclass metrics unless class `0` has been remapped away; SMP will reject ignored values inside the class range.

## Thresholds and Reductions

- Binary and multilabel metrics need either integer predictions or a threshold for floating probabilities.
- Multiclass metrics must not receive a threshold; use `logits.argmax(dim=1)`.
- `"micro"` is usually the safest headline IoU/F1 for imbalanced segmentation.
- `"macro"` highlights rare-class failures but can be noisy with empty classes.
- `"weighted"` reductions require `class_weights` and should be reviewed for class ordering.

## Empty Masks and `zero_division`

Dice/Jaccard-style losses zero out channels with no target pixels. Metrics may hit zero division when predictions and labels are all negative. Choose `zero_division` deliberately:

```python
iou = smp.metrics.iou_score(tp, fp, fn, tn, reduction="micro", zero_division=1.0)
f1 = smp.metrics.f1_score(tp, fp, fn, tn, reduction="macro", zero_division=0.0)
```

Use `zero_division="warn"` while debugging to surface empty-mask behavior.

## Device and Dtype Errors

- Move images, masks, model, loss weights, and metric tensors to compatible devices.
- Images and logits should be floating tensors.
- Multiclass targets must be `torch.long` class ids.
- Binary/multilabel BCE-style targets should be floating or binary-compatible tensors with the same shape as logits.
- `get_stats` requires integer targets; convert binary/multilabel metric targets with `.long()` after thresholding or validating `0/1` values.

## Difficult Synthetic Cases

Use these as usability tests for agents adapting this sub-skill:

1. Wrong binary loss on multiclass logits: create a model with `classes=3`, accidentally use `DiceLoss(BINARY_MODE)`, and require the agent to switch to `MULTICLASS_MODE` plus target `(N, H, W)` and `argmax` metrics.
2. Multilabel threshold/reduction with ignored pixels: create `(N, C, H, W)` multilabel targets with a void pixel, require `threshold=0.5` for metrics, explain why `get_stats(..., ignore_index=...)` is invalid, avoid unsafe `FocalLoss(mode="multilabel", ignore_index=...)`, and use `"micro"` vs `"macro"` reductions intentionally.
