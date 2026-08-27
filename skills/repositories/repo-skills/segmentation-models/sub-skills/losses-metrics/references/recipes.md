# Loss and metric recipes

These recipes assume Segmentation Models is used as a Keras package and that TensorFlow Keras is selected before import:

```python
import os
os.environ.setdefault("SM_FRAMEWORK", "tf.keras")

import numpy as np
import segmentation_models as sm
```

Use these snippets inside normal Keras `model.compile(...)` workflows. Model construction, preprocessing, data loading, generators, and training loops are intentionally out of scope for this sub-skill.

## Binary segmentation: sigmoid output

Use this when each pixel is foreground/background and the model output has `classes=1` and `activation="sigmoid"`.

```python
model = sm.Unet("resnet34", classes=1, activation="sigmoid")

model.compile(
    optimizer="Adam",
    loss=sm.losses.bce_jaccard_loss,
    metrics=[
        sm.metrics.IOUScore(threshold=0.5),
        sm.metrics.FScore(threshold=0.5),
        sm.metrics.Precision(threshold=0.5),
        sm.metrics.Recall(threshold=0.5),
    ],
)
```

Why this pairing works:

- `bce_jaccard_loss` combines pixelwise binary cross-entropy with a soft Jaccard loss.
- The losses see soft probabilities and remain differentiable.
- The metrics use `threshold=0.5` to report hard-mask IoU/F/precision/recall.

For deterministic validation of threshold behavior, run the bundled check with `--threshold-demo`.

## Binary class imbalance: focal + Dice/Jaccard

Use focal loss when the foreground is rare or false negatives/false positives need stronger optimization pressure.

```python
dice = sm.losses.DiceLoss()
focal = sm.losses.BinaryFocalLoss(alpha=0.75, gamma=2.0)
loss = dice + focal

model.compile(
    optimizer="Adam",
    loss=loss,
    metrics=[
        sm.metrics.IOUScore(threshold=0.5),
        sm.metrics.FScore(threshold=0.5),
    ],
)
```

Notes:

- Larger `alpha` increases the positive-class focal term in the binary focal implementation; the negative term uses `1 - alpha`.
- Larger `gamma` focuses more on hard examples.
- Built-in aliases such as `binary_focal_dice_loss` and `binary_focal_jaccard_loss` use default focal parameters. Instantiate the classes when you need different `alpha` or `gamma`.

## Single-label multiclass segmentation: softmax output

Use this when each pixel belongs to exactly one class and masks are one-hot encoded with `C=num_classes` channels.

```python
num_classes = 3  # for example: background, car, pedestrian
model = sm.Unet("resnet34", classes=num_classes, activation="softmax")

loss = sm.losses.cce_dice_loss
metrics = [
    sm.metrics.IOUScore(threshold=None),
    sm.metrics.FScore(threshold=None),
]

model.compile(optimizer="Adam", loss=loss, metrics=metrics)
```

Why `threshold=None` is often a safer default for softmax metrics:

- Segmentation Models metrics do not perform `argmax` conversion.
- A threshold such as `0.5` can zero out all classes for uncertain pixels whose highest softmax probability is below the threshold.
- If the evaluation policy requires argmax masks, convert predictions to one-hot outside these metrics or write a custom Keras metric for that policy.

## Multiclass with ignored background and class weighting

Assume channel `0` is background, channel `1` is car, and channel `2` is pedestrian.

For overlap losses and metrics, slice foreground channels with `class_indexes=[1, 2]`. When you pass `class_weights` together with `class_indexes`, provide weights for the selected channels only:

```python
foreground = [1, 2]
foreground_loss_weights = np.array([1.0, 2.0], dtype="float32")  # car, pedestrian

loss = (
    sm.losses.DiceLoss(class_indexes=foreground, class_weights=foreground_loss_weights)
    + sm.losses.CategoricalFocalLoss(class_indexes=foreground, alpha=0.25, gamma=2.0)
)

metrics = [
    sm.metrics.IOUScore(class_indexes=foreground, threshold=None),
    sm.metrics.FScore(class_indexes=foreground, threshold=None),
]

model.compile(optimizer="Adam", loss=loss, metrics=metrics)
```

If you use `CategoricalCELoss` and want to keep probability normalization over all softmax channels while ignoring the background contribution, use a full-length class-weight vector with background weight `0.0` instead of slicing first:

```python
ce = sm.losses.CategoricalCELoss(class_weights=np.array([0.0, 1.0, 2.0], dtype="float32"))
dice = sm.losses.DiceLoss(class_indexes=[1, 2], class_weights=np.array([1.0, 2.0], dtype="float32"))
loss = ce + dice
```

Reason: `CategoricalCELoss(class_indexes=...)` gathers selected channels before normalizing predictions along the class axis. That is useful only when you intentionally want normalization among the selected channels.

For reporting metrics, prefer unweighted foreground IoU/F-score unless you explicitly want a weighted diagnostic. Weighted overlap metrics are not normalized by the sum of weights and may exceed `1.0` if weights are greater than `1`.

## Multilabel multiclass segmentation: sigmoid output with multiple channels

Use this when classes can overlap or when channels are independent binary labels.

```python
num_labels = 3
model = sm.Unet("resnet34", classes=num_labels, activation="sigmoid")

loss = sm.losses.BinaryFocalLoss(alpha=0.5, gamma=2.0) + sm.losses.DiceLoss()
metrics = [
    sm.metrics.IOUScore(threshold=0.5),
    sm.metrics.FScore(threshold=0.5),
]

model.compile(optimizer="Adam", loss=loss, metrics=metrics)
```

Use `BinaryCELoss`/`BinaryFocalLoss` for independent sigmoid channels. Use `CategoricalCELoss`/`CategoricalFocalLoss` for one-hot softmax channels.

## Per-image versus per-batch reporting

For validation dashboards, choose `per_image=True` when each image should contribute equally regardless of object size:

```python
metrics = [sm.metrics.IOUScore(threshold=0.5, per_image=True)]
```

Choose `per_image=False` when the metric should aggregate over the full batch, so larger objects/images contribute more to the intersection and union:

```python
metrics = [sm.metrics.IOUScore(threshold=0.5, per_image=False)]
```

Use the same setting consistently across experiments. The values can differ, especially with empty masks or heterogeneous object sizes.

## Custom F-beta tradeoff

`FScore(beta=1)` is F1/Dice. Increase `beta` to emphasize recall, or decrease it to emphasize precision.

```python
metrics = [
    sm.metrics.FScore(beta=0.5, threshold=0.5, name="f0_5_score"),
    sm.metrics.FScore(beta=2.0, threshold=0.5, name="f2_score"),
]
```

Use custom names when Keras history keys need to be stable or human-readable.

## Direct tensor sanity check in notebooks or debugging sessions

When a task needs to confirm metric math before training, use tiny probability masks:

```python
gt = np.array([[[[1.0], [1.0], [0.0]],
                [[1.0], [1.0], [0.0]],
                [[0.0], [0.0], [0.0]]]], dtype="float32")

pr = np.array([[[[0.0], [0.0], [0.0]],
                [[1.0], [1.0], [0.0]],
                [[0.0], [0.0], [0.0]]]], dtype="float32")

iou = sm.metrics.IOUScore(smooth=1e-12)(gt, pr)
f1 = sm.metrics.FScore(beta=1, smooth=1e-12)(gt, pr)
```

Expected values are IoU `0.5` and F1/Dice `2/3`. The bundled `scripts/check_losses_metrics.py` performs this check through the selected Keras backend.
