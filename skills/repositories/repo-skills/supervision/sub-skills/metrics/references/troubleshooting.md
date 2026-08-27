# Metrics troubleshooting

Use this file when a metric import, compute call, result interpretation, or
benchmark loop behaves unexpectedly. For API details, see
[metrics reference](metrics-reference.md); for runnable patterns, see
[workflows](workflows.md).

## Pandas or metrics extra errors

**Symptoms**

- `.to_pandas()` raises an import error mentioning the metrics extra.
- The user installed only the base package and asks for tabular metric summaries.

**Fix**

Install the metrics extra:

```bash
pip install "supervision[metrics]"
```

Then rerun the Python process. If the task only needs numeric fields or
`print(result)`, `.to_pandas()` is optional.

## Missing class_id

**Symptoms**

- `ValueError` says a metric requires `class_id` on predictions, targets, or both.
- `ConfusionMatrix` says it can only be calculated for `Detections` with
  `class_id`.

**Why it happens**

Detection metrics are class-aware. Predictions and targets need `class_id` arrays
aligned with `xyxy`.

**Fix**

- For model outputs, route conversion to
  [detection-and-zones](../../detection-and-zones/SKILL.md) and ensure the
  adapter populates `class_id`.
- For dataset targets, route loading/conversion to [datasets](../../datasets/SKILL.md)
  and inspect `dataset.classes` plus each target's `class_id`.
- For class-agnostic mAP only, use `MeanAveragePrecision(class_agnostic=True)`.
  Do not use that option if class mistakes should be penalized.

## Missing prediction confidence

**Symptoms**

- `MeanAverageRecall`, `Precision`, `Recall`, `F1Score`, or `ConfusionMatrix`
  raises that predictions require `confidence`.
- mAR top-K values look wrong because all predictions have identical or missing
  ranking scores.

**Why it happens**

Metrics rank and threshold predictions by confidence. Targets do not need
confidence, but predictions do.

**Fix**

Populate `predictions.confidence` as a length-`N` numeric array aligned with
`xyxy`. If the source model has no confidence, either choose a defensible
constant and document the limitation or avoid confidence-ranked metrics.

## Wrong MetricTarget

**Symptoms**

- Segmentation mAP looks too high because boxes overlap while masks do not.
- Rotated boxes are scored as if they were axis-aligned boxes.
- `MetricTarget.MASKS` fails in `ConfusionMatrix`.

**Why it happens**

`MetricTarget.BOXES` uses only `detections.xyxy`. It ignores masks and OBB
corners even if they are present. `ConfusionMatrix` supports boxes and OBBs but
not masks.

**Fix**

- Use `MetricTarget.MASKS` for mask-overlap questions and provide masks on both
  predictions and targets.
- Use `MetricTarget.ORIENTED_BOUNDING_BOXES` for rotated-box questions and
  provide `ORIENTED_BOX_COORDINATES` data on both sides.
- Use `MetricTarget.BOXES` only when axis-aligned box quality is the intended
  metric.

## Mask requirements

**Symptoms**

- `ValueError` mentions `MetricTarget.MASKS` or detections needing masks.
- Mask metrics produce scores that match box overlap instead of mask overlap.

**Checklist**

1. Every non-empty prediction and target `Detections` has `detections.mask`.
2. The mask array is aligned with detections: shape starts with `N == len(detections)`.
3. The selected metric was constructed with `metric_target=MetricTarget.MASKS`.
4. The requested metric is not `ConfusionMatrix`; confusion matrices reject masks.

For mask size buckets, explicit `AREA_DATA_FIELD` metadata overrides pixel-count
area. Remove or fix stale area metadata if size-bucket results are surprising.

## Oriented-box requirements

**Symptoms**

- Error mentions `ORIENTED_BOUNDING_BOXES`, `ORIENTED_BOX_COORDINATES`, or
  malformed OBB element counts.
- OBB metrics behave like regular boxes.

**Checklist**

1. Import the constant: `from supervision.config import ORIENTED_BOX_COORDINATES`.
2. Store corners in `detections.data[ORIENTED_BOX_COORDINATES]` for predictions
   and targets.
3. Prefer shape `(N, 4, 2)` with corners ordered around the box. Confusion-matrix
   tensor conversion also accepts flat `(N, 8)`.
4. Construct the metric with `metric_target=MetricTarget.ORIENTED_BOUNDING_BOXES`.
5. Keep `xyxy`, `class_id`, and prediction `confidence` populated as normal.

If OBB data comes from a model adapter, use
[detection-and-zones](../../detection-and-zones/SKILL.md) to inspect the adapter
and confirm `ORIENTED_BOX_COORDINATES` is present.

## Class-id mapping and class list errors

**Symptoms**

- Scores are unexpectedly low despite high overlap.
- `ConfusionMatrix` raises about negative, non-integer, or out-of-range class ids.
- A perfect-overlap prediction appears as a wrong class.

**Why it happens**

Metrics are class-aware. Model class ids and dataset class ids must mean the same
thing before scoring. `ConfusionMatrix` indexes directly into the supplied
`classes` list and rejects ids outside that list.

**Fix**

- Print `dataset.classes`, prediction `class_id`, and target `class_id` for a few
  samples before computing metrics.
- Remap prediction ids to dataset ids before `Precision`, `Recall`, `F1Score`,
  `MeanAverageRecall`, or `ConfusionMatrix`.
- For mAP only, `MeanAveragePrecision(class_mapping={old_id: new_id})` can remap
  during preparation.
- Filter predictions for classes not present in the evaluation dataset when the
  benchmark intentionally ignores extra model classes.

## Per-class, macro, micro, and weighted confusion

**Symptoms**

- `MACRO`, `MICRO`, and `WEIGHTED` return different precision/recall/F1 values.
- A class that only appears in predictions changes `MACRO` but not `WEIGHTED`.
- Per-class arrays do not seem to match the printed class names.

**Explanation**

`matched_classes` is the authoritative row key for per-class arrays. It is not
always the same as `range(len(dataset.classes))`, especially with non-contiguous
ids or prediction-only classes.

- `MACRO` averages per-class scores equally.
- `MICRO` computes one score from total TP/FP/FN counts.
- `WEIGHTED` weights by target support, so prediction-only classes have weight
  zero. If no target support exists, the aggregate is `0.0`.

Always zip `matched_classes` with the per-class array instead of assuming row
position equals class id.

## Empty inputs and sentinel values

**Symptoms**

- mAP values are `-1`.
- Precision, recall, F1, or mAR values are `0.0` with empty per-class arrays.
- A size bucket returns no classes even though the overall metric has classes.

**Explanation**

The metrics intentionally define empty cases:

- `MeanAveragePrecision` uses a COCO-style `-1` sentinel when a result has no
  valid ground-truth support in the requested bucket/category.
- `MeanAverageRecall`, `Precision`, `Recall`, and `F1Score` return zero scores
  when there are no detections or no support.
- Size buckets are evaluated separately. A bucket can be empty even when the
  overall result is not.

Treat these as result semantics unless an input that should contain annotations
is unexpectedly empty.

## COCO area, iscrowd, and ignore surprises

**Symptoms**

- Small/medium/large mAP differs from the visible box sizes.
- A false positive inside a large crowd mask does not reduce mask mAP.
- A target exists but appears excluded from scoring.

**Why it happens**

`MeanAveragePrecision` follows COCO-style metadata when available:

- `AREA_DATA_FIELD` overrides computed geometry area.
- `detections.data["iscrowd"]` marks crowd targets.
- `detections.data["ignore"]` excludes targets from scoring.

**Fix**

Inspect `detections.data` on target batches. If the metadata came from a dataset
loader, route loader decisions to [datasets](../../datasets/SKILL.md). If the
metadata was hand-built, make sure each data array is one-dimensional and length
`N`.

## Confusion-matrix shape or tensor layout errors

**Symptoms**

- `from_tensors(...)` says predictions or targets have the wrong shape.
- Matrix dimensions are one larger than the class count.

**Expected layouts**

- Box predictions: `(N, 6)` rows `[x_min, y_min, x_max, y_max, class_id, confidence]`.
- Box targets: `(N, 5)` rows `[x_min, y_min, x_max, y_max, class_id]`.
- OBB predictions: `(N, 10)` rows `[x1, y1, x2, y2, x3, y3, x4, y4, class_id, confidence]`.
- OBB targets: `(N, 9)` rows `[x1, y1, x2, y2, x3, y3, x4, y4, class_id]`.

The extra matrix row and column are expected: false positives row, false
negatives column.

## Benchmark callback failures

**Symptoms**

- `ConfusionMatrix.benchmark(...)` fails inside the callback.
- Predictions are empty for every image.
- The benchmark tries to download a model or dataset.

**Fix**

Keep the callback small and deterministic: it must take one image array and
return one `Detections` object. Let sibling sub-skills handle prerequisites:

- Dataset path/schema issues: [datasets](../../datasets/SKILL.md).
- Model adapters and `Detections.from_*` conversion: [detection-and-zones](../../detection-and-zones/SKILL.md).
- Image/video I/O outside the dataset iterator: [media-utils](../../media-utils/SKILL.md).

Do not claim a full benchmark is runnable unless the user has supplied a local
dataset and a working local model callback.

## Visualization and plotting issues

**Symptoms**

- `.plot()` opens no window in a headless environment.
- The user wants saved false-positive/false-negative examples rather than a
  numeric score.
- Confusion-matrix labels are crowded or unreadable.

**Fix**

- Prefer numeric fields and `print(result)` for automated reports.
- Use `ConfusionMatrix.plot(save_path="cm.png", normalize=True)` for a saved
  heatmap.
- Use `ConfusionMatrix.benchmark(..., save_directory_path="evaluation-grids")`
  for per-image validation grids.
- For custom annotated outputs, use [annotators](../../annotators/SKILL.md) for
  drawing style and [media-utils](../../media-utils/SKILL.md) for file/video I/O.

## Legacy MeanAveragePrecision confusion

**Symptoms**

- Code uses `sv.MeanAveragePrecision.from_detections(...)` or imports from
  `supervision.metrics.detection`.
- Results differ from the newer update/compute mAP path.

**Fix**

For new code, use:

```python
from supervision.metrics import MeanAveragePrecision

result = MeanAveragePrecision().update(predictions, targets).compute()
```

Keep legacy calls only when maintaining older application code. For new mAP,
use the newer `supervision.metrics` class because it follows the current
COCO-style implementation and supports boxes, masks, OBBs, class mapping, and
size buckets.
