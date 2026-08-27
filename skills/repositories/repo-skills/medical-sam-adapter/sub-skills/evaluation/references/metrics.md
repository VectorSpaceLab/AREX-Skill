# Metric behavior

## Exact thresholding

`utils.eval_seg` applies `torch.sigmoid` to the decoder logits. For each
threshold in the fixed tuple:

```text
(0.1, 0.3, 0.5, 0.7, 0.9)
```

it thresholds both the prediction and the target with `> threshold`. It then
computes IoU on CPU NumPy integer masks and Dice on thresholded PyTorch masks.
The returned value is the arithmetic mean of the five threshold-specific
values. A printed IoU or Dice is therefore **threshold-averaged**, not the
score at 0.5 and not a probability calibration metric.

### IoU

For each batch item and channel, the source computes:

```text
intersection = (prediction AND target).sum((1, 2))
union        = (prediction OR target).sum((1, 2))
IoU          = mean((intersection + 1e-6) / (union + 1e-6))
```

The `1e-6` smoothing term applies to both numerator and denominator. Empty
prediction/target masks consequently receive a near-one score rather than an
undefined value. Interpret such cases with foreground prevalence and per-case
results; the aggregate can hide empty-mask behavior.

### Dice

`dice_coeff` sums the per-item `DiceCoeff` values in the batch and divides by
batch count. Each individual coefficient uses:

```text
(2 * dot(prediction, target) + 0.0001) /
(sum(prediction) + sum(target) + 0.0001)
```

The `0.0001` epsilon is different from the IoU smoothing value. Dice is
computed after thresholding, so it is also averaged over the five thresholds.
The source does not calculate a volume-weighted global confusion matrix.

## Return shapes and channel semantics

The return tuple depends on the number of channels `c` in the prediction:

| Prediction channels | `eval_seg` return order |
|---:|---|
| `c == 1` | `(IoU, Dice)` |
| `c == 2` | `(IoU_channel0, IoU_channel1, Dice_channel0, Dice_channel1)` |
| `c > 2` | `(IoU_channel0..IoU_channel[c-1], Dice_channel0..Dice_channel[c-1])` |

`validation_sam` accumulates the tuple and divides by `dataset_size`. It does
not attach class names to the `c > 2` tuple. Set `-multimask_output` to the
actual expected number of output channels and label channels yourself when
reporting multi-class results.

## REFUGE: cup/disc details

The `REFUGE` dataset class builds its target as:

```text
mask = concat([mask_cup, mask_disc], dim=0)
```

so the source-backed target channel order is **channel 0 cup, channel 1 disc**.
For two-channel evaluation, `eval_seg` returns channel 0's IoU, channel 1's
IoU, channel 0's Dice, and channel 1's Dice. `val.py` unpacks and prints these
as `IOU_CUP, IOU_DISC, DICE_CUP, DICE_DISC`, which is consistent with the
REFUGE loader's effective channel order. The local variable names inside
`eval_seg` call channel 0 `disc` and channel 1 `cup`; use the dataset
construction and returned order above rather than those internal variable
names when interpreting scores.

Use `-dataset REFUGE -multimask_output 2` for this route. The model's original
SAM decoder is constructed with two configured mask outputs and the validation
call requests multi-mask output when the value is greater than one. Do not
silently collapse the two channels to one score: report cup and disc
separately, and state that each is threshold-averaged.

## More than two classes

The `c > 2` branch is intended to evaluate every channel independently as a
binary mask. It does not perform an argmax across channels, does not calculate
an explicit background class, and does not compute a macro average for you. If
that branch completed, its intended return tuple would have `2*c` elements:
all per-channel IoUs followed by all per-channel Dice values.

However, the source currently reuses the local name `pred` for a NumPy slice
inside the channel loop. On the next threshold iteration the outer prediction
is no longer the original tensor, so the fixed five-threshold loop can fail on
a shape/indexing error. Treat `c > 2` independent metrics as a source
limitation requiring a reviewed source fix or a separately verified evaluator;
do not claim that a successful multi-class run is covered merely because
`-multimask_output` is greater than two. If the branch is repaired, calculate
any macro score explicitly from the returned channels and document whether
empty channels were included.

The original SAM path uses `multimask_output=(args.multimask_output > 1)` in
validation and its decoder is configured from `-multimask_output`. EfficientSAM
and MobileSAM explicitly pass `multimask_output=False` in `validation_sam`, even
when the argument is greater than one. Do not claim that setting the flag
creates multi-channel outputs for those variants without a verified model
output. If actual decoder channels differ from `args.multimask_output`, the
`validation_sam` accumulator shape can also become inconsistent; inspect the
model/checkpoint combination first.

## Loss versus metrics

`validation_sam` returns a first value accumulated from the configured loss and
a second value containing IoU/Dice metrics. `val.py` logs the first as `Total
score`; it is not an IoU/Dice aggregate. Compare like-for-like metric tuple
positions and the same dataset split, output size, threshold protocol, and
chunk policy. Scores from another evaluator using one threshold, argmax, a
single global confusion matrix, or a different empty-mask convention are not
numerically interchangeable.
