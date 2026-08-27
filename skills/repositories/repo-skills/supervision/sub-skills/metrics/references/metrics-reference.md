# Metrics reference

This reference covers the `supervision.metrics` APIs for detection-style
evaluation in `supervision` 0.31.0.dev0. Use it with the workflows in
[workflows](workflows.md) and failure guidance in
[troubleshooting](troubleshooting.md).

## Installation and imports

Install the metrics extra before using metrics APIs:

```bash
pip install "supervision[metrics]"
```

Prefer package-level metric imports:

```python
from supervision.metrics import (
    AveragingMethod,
    F1Score,
    MeanAveragePrecision,
    MeanAverageRecall,
    MetricTarget,
    Precision,
    Recall,
)
```

Use `sv.ConfusionMatrix` or `from supervision.metrics.detection import
ConfusionMatrix` for confusion matrices. Avoid new uses of top-level
`sv.MeanAveragePrecision`; that name maps to the legacy detection metric path.
Use `from supervision.metrics import MeanAveragePrecision` instead.

## Metric API table

| API | Purpose | Constructor | Compute input | Primary result fields |
| --- | --- | --- | --- | --- |
| `MeanAveragePrecision` | COCO-style average precision over IoU thresholds 0.50:0.95, including object-size buckets. | `MeanAveragePrecision(metric_target=MetricTarget.BOXES, class_agnostic=False, class_mapping=None, image_indices=None)` | Accumulate prediction/target `Detections` with `update(...)`, then call `compute()`. | `map50_95`, `map50`, `map75`, `mAP_scores`, `ap_per_class`, `matched_classes`, `small_objects`, `medium_objects`, `large_objects`. |
| `MeanAverageRecall` | COCO-style average recall with top-K prediction limits per image. | `MeanAverageRecall(metric_target=MetricTarget.BOXES)` | Same update/compute pattern. | `mAR_at_1`, `mAR_at_10`, `mAR_at_100`, `recall_scores`, `recall_per_class`, `matched_classes`, size buckets. |
| `Precision` | Detection precision `TP / (TP + FP)` at ten IoU thresholds. | `Precision(metric_target=MetricTarget.BOXES, averaging_method=AveragingMethod.WEIGHTED)` | Same update/compute pattern. | `precision_at_50`, `precision_at_75`, `precision_scores`, `precision_per_class`, `matched_classes`, size buckets. |
| `Recall` | Detection recall `TP / (TP + FN)` at ten IoU thresholds. | `Recall(metric_target=MetricTarget.BOXES, averaging_method=AveragingMethod.WEIGHTED)` | Same update/compute pattern. | `recall_at_50`, `recall_at_75`, `recall_scores`, `recall_per_class`, `matched_classes`, size buckets. |
| `F1Score` | Harmonic mean of precision and recall at ten IoU thresholds. | `F1Score(metric_target=MetricTarget.BOXES, averaging_method=AveragingMethod.WEIGHTED)` | Same update/compute pattern. | `f1_50`, `f1_75`, `f1_scores`, `f1_per_class`, `matched_classes`, size buckets. |
| `ConfusionMatrix` | Class-aware confusion matrix with a background row/column for false positives and false negatives. | Construct with `ConfusionMatrix.from_detections(...)`, `from_tensors(...)`, or `benchmark(...)`. | Lists of predictions and targets, tensors, or a `DetectionDataset` plus callback. | `matrix`, `classes`, `conf_threshold`, `iou_threshold`, `metric_target`, `.plot(...)`. |

All metric classes implement `update(...)`, `reset()`, and `compute()`. `update`
accepts either one `Detections` pair or two equally long lists of `Detections`.
It returns the metric instance, so chaining is valid.

## Required Detections fields

| Use case | Predictions need | Targets need | Notes |
| --- | --- | --- | --- |
| Box metrics | `xyxy`, `class_id`, `confidence` | `xyxy`, `class_id` | Default `MetricTarget.BOXES`; masks and OBB metadata are ignored. |
| Mask metrics | `xyxy`, `mask`, `class_id`, `confidence` | `xyxy`, `mask`, `class_id` | Use `MetricTarget.MASKS`. `ConfusionMatrix` does not support masks. |
| OBB metrics | `xyxy`, `data[ORIENTED_BOX_COORDINATES]`, `class_id`, `confidence` | `xyxy`, `data[ORIENTED_BOX_COORDINATES]`, `class_id` | Use `MetricTarget.ORIENTED_BOUNDING_BOXES`. Store corners as `(N, 4, 2)`; confusion-matrix tensor conversion also accepts flat `(N, 8)`. |
| Confusion matrix from tensors | rows shaped `(N, 6)` for boxes or `(N, 10)` for OBB predictions | rows shaped `(N, 5)` for boxes or `(N, 9)` for OBB targets | Tensor row order is coordinates, `class_id`, and optional `confidence` for predictions. |

Import constants instead of hard-coded names when writing aligned detection data:

```python
from supervision.config import AREA_DATA_FIELD, ORIENTED_BOX_COORDINATES
```

`Detections.data` arrays must stay aligned with `xyxy`: one element per
detection. If the task starts from model outputs, route construction to
[detection-and-zones](../../detection-and-zones/SKILL.md). If the task starts
from annotation files, route loading to [datasets](../../datasets/SKILL.md).

## MetricTarget behavior

| Target | Data source | Supported by | Typical mistake |
| --- | --- | --- | --- |
| `MetricTarget.BOXES` | `detections.xyxy` | All metrics and `ConfusionMatrix`. | Using it for segmentation/OBB results and expecting mask or rotated-box IoU. |
| `MetricTarget.MASKS` | `detections.mask` | `MeanAveragePrecision`, `MeanAverageRecall`, `Precision`, `Recall`, `F1Score`. | Passing detections without masks, or trying to use it with `ConfusionMatrix`. |
| `MetricTarget.ORIENTED_BOUNDING_BOXES` | `detections.data[ORIENTED_BOX_COORDINATES]` | All new metrics and `ConfusionMatrix`. | Storing only axis-aligned `xyxy`, malformed OBB shape, or missing OBB data on one side. |

When `MetricTarget.BOXES` is selected, metrics intentionally use axis-aligned
boxes even if masks or OBB corners are also present. Select the target that
matches the quality question the user is asking.

## Class matching and class ids

New metrics match predictions to targets only when both IoU and `class_id` match.
A wrong-class prediction with perfect overlap is therefore not a true positive
for mAP, mAR, precision, recall, or F1. Predictions are sorted by descending
confidence where ranking matters, and matching is greedy one-to-one.

`Precision`, `Recall`, and `F1Score` expose `matched_classes` as the sorted union
of classes appearing in predictions or targets. This matters for background
images and classes predicted but never present in ground truth:

- `AveragingMethod.MICRO` merges total TP/FP/FN counts before computing the
  scalar score.
- `AveragingMethod.MACRO` computes each class score and averages classes equally.
  Prediction-only classes contribute a zero score.
- `AveragingMethod.WEIGHTED` weights by target support. Classes with no target
  support have weight zero; if no target support exists anywhere, the aggregate
  score is `0.0`.

`ConfusionMatrix` requires an explicit `classes` list and validates class ids as
finite integers in `[0, len(classes) - 1]`. Its matrix has shape
`(len(classes) + 1, len(classes) + 1)`. The last row represents false positives;
the last column represents false negatives. Cross-class spatial matches populate
the true-class row and predicted-class column.

## Result interpretation

### MeanAveragePrecisionResult

- `map50_95` is the average over IoU thresholds `0.50, 0.55, ..., 0.95`.
- `map50` and `map75` are single-threshold summaries.
- `ap_per_class` rows align with `matched_classes`.
- `small_objects`, `medium_objects`, and `large_objects` are nested result
  objects for COCO size buckets: small `< 32^2`, medium `32^2 <= area < 96^2`,
  large `>= 96^2`.
- `-1` is a sentinel for no valid COCO support in the requested bucket/category;
  it is not a Python error by itself.

### MeanAverageRecallResult

- `mAR_at_1`, `mAR_at_10`, and `mAR_at_100` limit predictions per image, not per
  class.
- `recall_per_class` has shape `(3, num_classes, 10)` for the three top-K limits
  and ten IoU thresholds.
- Empty inputs return zero recall scores with no matched classes.

### PrecisionResult, RecallResult, and F1ScoreResult

- Scalar shortcuts are `precision_at_50` / `precision_at_75`, `recall_at_50` /
  `recall_at_75`, and `f1_50` / `f1_75`.
- Per-class arrays have shape `(num_classes, 10)` and rows align with
  `matched_classes`.
- Empty inputs return zeros with empty per-class arrays.
- Size buckets are computed using explicit `AREA_DATA_FIELD` metadata when
  present; otherwise boxes use box area, masks use mask pixel count, and OBBs use
  polygon area.

## COCO-style metadata

`MeanAveragePrecision` internally prepares COCO-style evaluation records. It
uses these optional target fields from `detections.data` when present:

| Field | Effect |
| --- | --- |
| `AREA_DATA_FIELD` (usually the `"area"` data key) | Overrides computed area for size-bucket assignment. Must be one-dimensional and aligned with detections. |
| `"iscrowd"` | Marks crowd ground truth. For mask mAP, detections contained in a crowd mask can be ignored rather than counted as false positives. |
| `"ignore"` | Excludes marked targets from scoring. |

COCO loaders can populate area and crowd-style metadata. Let the
[datasets](../../datasets/SKILL.md) sub-skill own loading choices such as COCO
`use_iscrowd`; use this sub-skill to explain how the metadata affects metrics.

`MeanAveragePrecision` also supports:

- `class_mapping={old_id: new_id}` to remap class ids during mAP preparation.
- `class_agnostic=True` to evaluate all detections as a single class.
- `image_indices=[...]` to preserve external image ids when preparing records.

For `Precision`, `Recall`, `F1Score`, `MeanAverageRecall`, and `ConfusionMatrix`,
remap `Detections.class_id` before calling `update(...)` or `from_detections(...)`.

## COCOEvaluator and EvaluationDataset

`EvaluationDataset` and `COCOEvaluator` live in the mAP implementation module and
are lower-level support classes for COCO-style evaluation. Prefer
`MeanAveragePrecision` for normal user workflows. Reach for these classes only
when the caller already has COCO-like dictionaries and explicitly asks to debug
the evaluator internals or reproduce prepared evaluation records.

## Pandas and plotting

All new metric result classes provide `.to_pandas()` and `.plot()`:

- `.to_pandas()` requires pandas from `pip install "supervision[metrics]"` and
  returns one summary row. It does not replace the per-class arrays when the user
  needs full per-class analysis.
- `.plot()` lazily imports plotting support and displays a summary bar chart for
  the result and size buckets. It is optional; numeric fields and `str(result)`
  are the stable outputs.
- `ConfusionMatrix.plot(save_path=None, title=None, classes=None,
  normalize=False, fig_size=(12, 10))` returns a figure and can save a heatmap.
