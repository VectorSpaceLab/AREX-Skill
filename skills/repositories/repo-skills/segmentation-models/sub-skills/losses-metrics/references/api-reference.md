# Losses and metrics API reference

This reference is distilled for Segmentation Models version 1.0.1 with the TensorFlow Keras framework selected through `SM_FRAMEWORK=tf.keras` before import.

## Framework and object initialization

Segmentation Models supports either standalone `keras` or `tf.keras`. In modern TensorFlow environments, set the framework before importing the package:

```python
import os
os.environ.setdefault("SM_FRAMEWORK", "tf.keras")
import segmentation_models as sm
```

Loss and metric classes inherit from Segmentation Models `KerasObject`. Construction requires initialized Keras backend/layers/models/utils submodules. If objects are constructed before framework initialization succeeds, the package raises `RuntimeError: You cannot use KerasObjects with None submodules.`

## Tensor conventions

- Inputs are Keras tensors or arrays shaped as image batches: channels-last `(B, H, W, C)` by default, or channels-first `(B, C, H, W)` if the Keras backend image data format is changed.
- The channel axis is the class axis. For binary segmentation use `C=1`; for single-label multiclass segmentation use one-hot masks with `C=num_classes`; for multilabel segmentation use independent binary channels.
- Prediction tensors should already be probabilities from a compatible model activation (`sigmoid` or `softmax`), not raw logits.

## Metric classes and aliases

| API | Main purpose | Default Keras name |
| --- | --- | --- |
| `IOUScore(class_weights=None, class_indexes=None, threshold=None, per_image=False, smooth=1e-05, name=None)` | Jaccard / intersection-over-union score. | `iou_score` |
| `FScore(beta=1, class_weights=None, class_indexes=None, threshold=None, per_image=False, smooth=1e-05, name=None)` | Dice/F-beta score. `beta=1` is F1/Dice; `beta=2` weights recall more. | `f{beta}-score` |
| `Precision(class_weights=None, class_indexes=None, threshold=None, per_image=False, smooth=1e-05, name=None)` | True positives divided by predicted positives. | `precision` |
| `Recall(class_weights=None, class_indexes=None, threshold=None, per_image=False, smooth=1e-05, name=None)` | True positives divided by ground-truth positives. | `recall` |

Metric aliases are already-constructed callable objects:

```python
sm.metrics.iou_score      # IOUScore()
sm.metrics.f1_score       # FScore(beta=1)
sm.metrics.f2_score       # FScore(beta=2)
sm.metrics.precision      # Precision()
sm.metrics.recall         # Recall()
```

Instantiate classes instead of using aliases whenever a task needs non-default `threshold`, `class_indexes`, `class_weights`, `per_image`, `smooth`, or `name`.

## Loss classes, aliases, and combinations

| API | Main purpose | Default Keras name |
| --- | --- | --- |
| `JaccardLoss(class_weights=None, class_indexes=None, per_image=False, smooth=1e-05)` | `1 - IOUScore(...)`, always uses soft predictions with no threshold. | `jaccard_loss` |
| `DiceLoss(beta=1, class_weights=None, class_indexes=None, per_image=False, smooth=1e-05)` | `1 - FScore(beta=...)`, always uses soft predictions with no threshold. | `dice_loss` |
| `BinaryCELoss()` | Mean binary cross-entropy over all pixels/channels. | `binary_crossentropy` |
| `CategoricalCELoss(class_weights=None, class_indexes=None)` | Mean categorical cross-entropy over the class axis after probability normalization and clipping. | `categorical_crossentropy` |
| `BinaryFocalLoss(alpha=0.25, gamma=2.0)` | Binary focal loss with positive weight `alpha`, negative weight `1 - alpha`, and focusing exponent `gamma`. | `binary_focal_loss` |
| `CategoricalFocalLoss(alpha=0.25, gamma=2.0, class_indexes=None)` | Multiclass focal loss over one-hot channels. | `focal_loss` |

Loss aliases are already-constructed callable objects:

```python
sm.losses.jaccard_loss
sm.losses.dice_loss
sm.losses.binary_focal_loss
sm.losses.categorical_focal_loss
sm.losses.binary_crossentropy
sm.losses.categorical_crossentropy
```

Built-in combined loss aliases are sums of `Loss` objects:

```python
sm.losses.bce_dice_loss
sm.losses.bce_jaccard_loss
sm.losses.cce_dice_loss
sm.losses.cce_jaccard_loss
sm.losses.binary_focal_dice_loss
sm.losses.binary_focal_jaccard_loss
sm.losses.categorical_focal_dice_loss
sm.losses.categorical_focal_jaccard_loss
```

Custom combinations use `+` between Segmentation Models `Loss` objects and scalar multiplication by an `int` or `float`:

```python
loss = sm.losses.DiceLoss(class_indexes=[1, 2]) + 0.5 * sm.losses.BinaryFocalLoss(alpha=0.75)
```

## Formulas

All overlap metrics first slice requested channels, optionally threshold predictions, then reduce over spatial dimensions and optionally the batch dimension.

- Intersection: `sum(gt * pr)`
- Union for IoU: `sum(gt + pr) - intersection`
- True positives: `tp = sum(gt * pr)`
- False positives: `fp = sum(pr) - tp`
- False negatives: `fn = sum(gt) - tp`

Metric formulas:

```text
IoU/Jaccard = (intersection + smooth) / (union + smooth)
F_beta      = ((1 + beta^2) * tp + smooth) / ((1 + beta^2) * tp + beta^2 * fn + fp + smooth)
Precision   = (tp + smooth) / (tp + fp + smooth)
Recall      = (tp + smooth) / (tp + fn + smooth)
```

Loss formulas:

```text
JaccardLoss          = 1 - IoU/Jaccard, with threshold=None
DiceLoss             = 1 - F_beta, with threshold=None
BinaryCELoss         = mean(binary_crossentropy(gt, pr))
CategoricalCELoss    = -mean(gt * log(normalized_and_clipped_pr) * class_weights)
BinaryFocalLoss      = mean(-gt * alpha * (1-pr)^gamma * log(pr)
                         -(1-gt) * (1-alpha) * pr^gamma * log(1-pr))
CategoricalFocalLoss = mean(-gt * alpha * (1-pr)^gamma * log(pr))
```

## Parameter semantics

### `class_indexes`

`class_indexes` selects channels before metric/loss computation. It can be a single integer or a list of integers. Use it to ignore background channels or report only target foreground classes.

Examples:

```python
# Report only foreground classes 1 and 2, ignoring background channel 0.
metric = sm.metrics.IOUScore(class_indexes=[1, 2])
loss = sm.losses.DiceLoss(class_indexes=[1, 2])
```

For channels-last tensors, indexes refer to the last dimension. For channels-first tensors, indexes refer to the second dimension.

### `class_weights`

`class_weights` multiplies the per-class score/loss after channel selection for overlap metrics/losses. Its length should match the number of selected classes, not necessarily the original number of channels. If `class_indexes=None`, use one weight per channel.

Important scaling behavior: overlap metric weights are multipliers before the final mean, not normalized probabilities. Weights greater than `1` can make a weighted metric exceed the usual `[0, 1]` reporting range. Use unweighted metrics for dashboards when bounded scores matter, and use weighted losses when the goal is optimization pressure.

For `CategoricalCELoss`, weights multiply the one-hot cross-entropy term. If you want to keep softmax normalization over all channels while ignoring background, prefer a full-length weight vector with a zero background weight:

```python
ce = sm.losses.CategoricalCELoss(class_weights=[0.0, 1.0, 2.0])
```

Passing `class_indexes` to `CategoricalCELoss` slices channels before normalization, so selected probabilities are renormalized among only the selected channels.

### `threshold`

`threshold` is available on metrics only. When it is not `None`, predictions are converted with a strict `pr > threshold` comparison and cast back to the Keras floating dtype before IoU/F-score/precision/recall math.

Losses do not accept or apply `threshold`; Jaccard and Dice losses call the same overlap formulas with `threshold=None` so optimization remains differentiable.

### `per_image`

- `per_image=False` aggregates intersections, unions, true positives, false positives, and false negatives over the whole batch before averaging classes.
- `per_image=True` computes per-image per-class scores first, averages over images, applies class weights, then averages classes.

The two modes can differ when images have different object sizes or empty masks.

### `smooth`

`smooth` prevents division by zero. With the default `1e-05`, an empty ground truth and empty prediction produce an overlap score of `1.0`; an empty ground truth with non-empty predictions produces a score near `0.0` when the prediction sum is much larger than `smooth`.

Use tiny `smooth` values for deterministic math assertions. Use the default unless there is a specific numerical-stability reason to change it.

### `beta`

`beta` is used by `FScore` and `DiceLoss`. `beta=1` gives F1/Dice. Values greater than `1` increase recall weight; values less than `1` increase precision weight.

### `alpha` and `gamma`

`alpha` and `gamma` are focal-loss parameters. `alpha` controls class imbalance weighting. `gamma` down-weights already confident predictions as it increases. The package defaults are `alpha=0.25` and `gamma=2.0`.

## Deterministic expected values

For a binary `3x3` mask with four ground-truth positives and a prediction that captures two of them without false positives:

```text
TP=2, FP=0, FN=2
IoU       = 2 / (2 + 0 + 2) = 0.5
F1/Dice   = 2*TP / (2*TP + FP + FN) = 2/3
F2        = 5*TP / (5*TP + 4*FN + FP) = 5/9
Precision = 1.0
Recall    = 0.5
JaccardLoss = 0.5
DiceLoss    = 1/3
```

The bundled `scripts/check_losses_metrics.py` asserts these values with small deterministic tensors.
