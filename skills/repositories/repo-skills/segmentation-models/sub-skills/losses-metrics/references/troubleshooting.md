# Losses and metrics troubleshooting

Use this guide when Segmentation Models compiles but metrics look wrong, losses do not match the task, or Keras raises errors around custom loss/metric objects.

## Framework or submodule initialization errors

Symptoms:

- `RuntimeError: You cannot use KerasObjects with None submodules.`
- Import picks standalone `keras` when the project expects `tf.keras`.
- Aliases such as `sm.losses.dice_loss` or `sm.metrics.iou_score` fail during construction or use.

Fix:

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"  # set before importing segmentation_models
import segmentation_models as sm
```

If the package has already been imported with the wrong framework in a long-running Python process, restart the process and set `SM_FRAMEWORK` before import. Avoid mixing standalone `keras` tensors/models with `tf.keras` losses and metrics.

## Shape and channel-order mistakes

Symptoms:

- Metrics are unexpectedly low even on visually correct predictions.
- `class_indexes` selects the wrong class.
- Broadcasting or shape errors appear when class weights are applied.

Checks:

- Binary masks should usually be `(B, H, W, 1)` for channels-last, not `(B, H, W)`.
- Softmax multiclass masks should be one-hot `(B, H, W, C)`, not integer label maps `(B, H, W)`.
- If the Keras backend image data format is `channels_first`, tensors should be `(B, C, H, W)` and class indexes refer to axis `1`.
- Prediction and ground-truth tensors must have the same shape and class order.

Fix integer multiclass masks before calling Segmentation Models metrics/losses:

```python
# Example for TensorFlow Keras utilities
# y_integer shape: (B, H, W), values in [0, num_classes-1]
y_one_hot = tf.keras.utils.to_categorical(y_integer, num_classes=num_classes)
```

## Wrong activation/loss pairing

Symptoms:

- Training loss is unstable or does not decrease.
- Categorical losses behave poorly on sigmoid multilabel outputs.
- Binary losses are used with softmax one-hot outputs by accident.

Recommended pairings:

| Task | Output activation | Compatible losses |
| --- | --- | --- |
| Binary foreground/background | `sigmoid`, `classes=1` | `BinaryCELoss`, `BinaryFocalLoss`, `DiceLoss`, `JaccardLoss`, `bce_*`, `binary_focal_*` |
| Single-label multiclass | `softmax`, `classes=C` | `CategoricalCELoss`, `CategoricalFocalLoss`, `DiceLoss`, `JaccardLoss`, `cce_*`, `categorical_focal_*` |
| Multilabel overlapping classes | `sigmoid`, `classes=C` | `BinaryCELoss`, `BinaryFocalLoss`, `DiceLoss`, `JaccardLoss` |

Segmentation Models loss implementations expect probabilities, not logits. Use a model activation or a custom loss that explicitly handles logits.

## Threshold confusion

Symptoms:

- Metrics differ from manual argmax evaluation.
- Softmax multiclass metrics are zero for uncertain predictions.
- Changing threshold has no effect on loss.

Facts:

- `threshold` exists on `IOUScore`, `FScore`, `Precision`, and `Recall` only.
- Thresholding uses strict `prediction > threshold`; values exactly equal to the threshold become `0`.
- Jaccard and Dice losses always use soft predictions with `threshold=None`.
- Segmentation Models does not apply `argmax` inside multiclass metrics.

Fixes:

- For binary or multilabel sigmoid metrics, use `threshold=0.5` unless the task defines another cutoff.
- For softmax multiclass metrics, start with `threshold=None` for soft scores, or convert predictions to one-hot argmax masks outside the metric if hard multiclass scoring is required.
- Do not expect threshold changes to alter training loss.

## Class indexes and class weights

Symptoms:

- `ValueError`/broadcast errors for class weights.
- Weighted metrics exceed `1.0`.
- Background is not actually ignored.
- Categorical cross-entropy changes unexpectedly when `class_indexes` is set.

Facts and fixes:

- `class_indexes` slices channels before computation.
- For overlap metrics/losses, `class_weights` length should match the selected channel count. With `class_indexes=[1, 2]`, pass two weights, not a full three-class vector.
- Overlap metric weights are multipliers before a mean, not normalized by their sum. Weights greater than `1` can produce weighted diagnostic values above `1.0`.
- For reporting, use unweighted metrics or weights chosen for the desired scale. For optimization, weighted losses are often more appropriate.
- `CategoricalCELoss(class_indexes=...)` slices channels before normalizing predictions; if you want full softmax normalization but zero background loss contribution, use a full-length vector such as `class_weights=[0.0, 1.0, 2.0]` and leave `class_indexes=None`.

## All-zero masks and `smooth`

Symptoms:

- Empty ground truth and empty prediction give IoU/F-score `1.0`.
- Empty ground truth and a small non-empty prediction produce a tiny non-zero score rather than exact zero.
- Tiny objects are sensitive to the `smooth` value.

Explanation:

`smooth` is added to numerator and denominator to avoid division by zero. This makes an empty/empty comparison a perfect score and keeps empty/non-empty comparisons finite.

Fixes:

- Keep the default `smooth=1e-05` for normal training unless there is a clear reason to change it.
- Use a very small `smooth`, such as `1e-12`, only for deterministic math checks.
- Track empty-mask cases separately if they have special business meaning.

## Per-image versus per-batch differences

Symptoms:

- Validation IoU changes when batch size changes or image composition changes.
- Manual per-image averaging does not match the Keras metric.

Facts:

- `per_image=False` reduces over the whole batch before scoring.
- `per_image=True` scores each image first, averages over images, then applies class weighting and class averaging.

Fix:

Choose one policy and keep it stable across experiments. Use `per_image=True` when each image should count equally; use `per_image=False` when large masks should contribute proportionally to their pixels.

## Combined loss object mistakes

Symptoms:

- Adding a Python string loss to a Segmentation Models loss object fails.
- Built-in combined aliases do not use the desired focal alpha/gamma or class weights.
- Keras history names are unexpected.

Fixes:

- Combine Segmentation Models `Loss` objects with `+`; do not add strings.
- Instantiate classes for custom parameters, then combine them:

```python
loss = sm.losses.DiceLoss(class_indexes=[1, 2]) + 0.5 * sm.losses.CategoricalFocalLoss(class_indexes=[1, 2])
```

- Use custom metric names when Keras history keys need to be stable:

```python
metric = sm.metrics.FScore(beta=2, threshold=0.5, name="f2_score")
```

## Numeric dtype and clipping issues

Symptoms:

- Cross-entropy or focal losses produce NaNs.
- Predictions are outside `[0, 1]`.

Facts:

- Categorical cross-entropy and focal losses clip probabilities internally to Keras epsilon boundaries.
- Binary cross-entropy delegates to the Keras backend implementation.
- The losses still assume probability-like predictions. Raw logits or incorrectly scaled masks can break expectations.

Fix:

Use `sigmoid` or `softmax` output activations for standard workflows, make masks `float32`, and verify that ground truth is binary/one-hot as appropriate.

## Quick local sanity command

To distinguish API misuse from data/model issues, run the bundled deterministic check in the same environment as training:

```bash
python scripts/check_losses_metrics.py --threshold-demo
```

If the script passes but training metrics look wrong, focus on mask shape, channel order, activation/loss pairing, threshold policy, and dataset preprocessing.
