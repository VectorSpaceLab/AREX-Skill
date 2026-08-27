# Metrics, pairing, and output interpretation

## ISIC output names and pairing

The source sampler writes the ensemble image as
`<slice_ID>_output_ens.jpg`. For an ISIC loader name such as
`ISIC_0000003.jpg`, the source extracts `slice_ID=0000003`; the original
ISIC evaluator then derives the ground-truth name as
`ISIC_0000003_Segmentation.png` by taking the prediction filename's first
underscore-delimited token. This is a filename convention, not content-based
matching.

The source evaluator walks the prediction tree and considers every file whose
name contains the literal substring `ens`. It does not filter by extension,
validate one-to-one IDs, or sort traversal. The bundled evaluator keeps the
same `ens` and first-token assumptions but sorts paths for deterministic output,
requires readable image files, reports missing ground truths, and fails
explicitly when no pairs remain. Keep prediction and ground-truth directories
separate. Do not let an old ensemble image or a debug image accidentally share
the expected token.

The source expects 256x256 predictions in practice: it leaves the prediction
size unchanged and resizes each ground truth to `(256, 256)`. The bundled
`evaluate_isic.py` and `evaluate_per_class.py` expose `--image-size` (default
`256`) so tiny fixtures can use a smaller explicit size. Predictions must match
the selected size; an accidental mismatch is an actionable error rather than a
silent geometric comparison.

## Intended IoU/Dice threshold averaging

For each matched pair, the source `eval_seg` evaluates thresholds
`(0.1, 0.3, 0.5, 0.7, 0.9)`. At every threshold:

1. Convert the prediction and ground truth to binary masks with `> threshold`.
2. IoU is `(intersection + 1e-6) / (union + 1e-6)`, computed per batch image
   and then averaged.
3. Dice uses the source torch implementation with an epsilon of `0.0001`:
   `(2 * intersection + 0.0001) / (sum(pred) + sum(gt) + 0.0001)`.
4. Average each metric over the five thresholds, then average those per-pair
   results over all matched pairs.

The bundled ISIC evaluator preserves those thresholds and epsilon conventions,
but makes two undefined cases explicit:

- no matched pairs is an error with a nonzero exit status, instead of dividing
  by zero for `num == 0`;
- a prediction whose maximum intensity is zero is treated as an all-zero mask,
  not divided by zero to produce NaNs. This is a defensive interpretation of
the source's `pred / pred.max()` line and is reported in the run summary.

A completely empty pair can legitimately produce IoU and Dice close to 1 under
the source's smoothing terms. That is a mathematical consequence of the
thresholded metric, not evidence that foreground segmentation succeeded.
Inspect foreground occupancy and per-class results before accepting a score.

Missing ground-truth files are errors by default. An explicit
`--allow-missing` mode can skip them for exploratory audits, but a skipped file
must be reported and a run with zero usable pairs still fails. Do not silently
average a partial benchmark as if it were complete.

## Per-class two-class metrics

`segmentation_env_PerClass.py` builds a two-class histogram with `num_classes=2`
and reports:

- `aAcc`: total correctly classified pixels divided by total labeled pixels;
- `IoU`: intersection divided by union for each class;
- `Precision`: intersection divided by predicted pixels for each class;
- `Recall`: intersection divided by labeled pixels for each class; and
- `Fscore`: beta-1 F-score from precision and recall.

The source labels its columns `class1` and `class2`; the first is conventionally
background and the second foreground for a binary mask, but the source does
not attach semantic names. The bundled evaluator uses explicit `class0`
(background) and `class1` (foreground) labels and prints a summary plus the
number of pairs. Pass prediction and ground-truth directories separately with
`--inp-pth` and `--out-pth`; each prediction `foo.<image>` maps to
`foo.tif` under the ground-truth directory. Its input is bounded to two classes:
greyscale prediction and ground-truth images are scaled to `[0, 1]`, thresholded
into background/foreground, and accumulated across at most `--limit` pairs
(default 10000).
It does not import mmseg, torch, torchvision, prettytable, or any project
module.

The source's ground truth is divided by 255 before the histogram call, so an
ordinary 0/255 mask is effectively binary. Its `label != 255` ignore rule is
therefore not useful after normalization; the bundled evaluator does not infer
an ignore class from raw 255 pixels. If an ignore label is needed, preprocess
it explicitly or extend the bounded script and record that deviation.

For robust reporting, the bundled evaluator prints `NA` for a class whose
metric denominator is zero (for example, no foreground in either prediction or
label), rather than emitting an unannotated `nan` from a tensor division. Such
classes must not be silently dropped from a comparison. The optional
`prettytable` dependency used by the source is intentionally not required.

## STAPLE and intensity caveats

The sampler's `staple` helper receives an `N,C,H,W` tensor and initially
computes a mean over ensemble members. It performs one reweighting pass only
when its internal gap test exceeds `0.02`; the implementation is a lightweight
mean-vote refinement, not a guarantee of statistically estimated STAPLE
parameters. The saved aggregate is an intensity JPEG. Evaluation therefore
normalizes by the per-image maximum and thresholds repeatedly; the JPEG codec,
normalization, and choice of `version` can affect results.

Do not compare an individual debug member with an aggregate under the same
metric without recording which version path produced it. New versions ensemble
the sampled final channel; legacy versions ensemble `cal_out`, which includes
source-specific calibration. A zero-valued aggregate is handled safely by the
bundled evaluator but is a warning about output quality or a failed sample.
