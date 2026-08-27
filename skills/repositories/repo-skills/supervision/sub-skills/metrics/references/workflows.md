# Metrics workflows

Use these workflows after confirming the user has prediction and target
`Detections` aligned by image. Route data loading to [datasets](../../datasets/SKILL.md)
and model-result normalization to
[detection-and-zones](../../detection-and-zones/SKILL.md).

## Install and smoke check

```bash
pip install "supervision[metrics]"
```

```python
import supervision as sv
from supervision.metrics import MeanAveragePrecision, MetricTarget

metric = MeanAveragePrecision(metric_target=MetricTarget.BOXES)
print(metric)
```

If import works but `.to_pandas()` fails, check the metrics extra in
[troubleshooting](troubleshooting.md#pandas-or-metrics-extra-errors).

## Prepare prediction and target pairs

Metric inputs are per-image pairs. For each image, predictions and targets are
separate `Detections` objects:

```python
import numpy as np
import supervision as sv

predictions = sv.Detections(
    xyxy=np.array([[10, 10, 50, 50], [70, 70, 120, 120]], dtype=np.float32),
    confidence=np.array([0.92, 0.60], dtype=np.float32),
    class_id=np.array([0, 1], dtype=np.int32),
)

targets = sv.Detections(
    xyxy=np.array([[10, 10, 50, 50]], dtype=np.float32),
    class_id=np.array([0], dtype=np.int32),
)
```

For a dataset, accumulate lists in the same image order:

```python
prediction_batches: list[sv.Detections] = []
target_batches: list[sv.Detections] = []

for image_path, image, targets in dataset:
    predictions = predict_as_detections(image)
    prediction_batches.append(predictions)
    target_batches.append(targets)
```

Do not shuffle one list without applying the same operation to the other list.

## Compute mAP

```python
from supervision.metrics import MeanAveragePrecision, MetricTarget

map_metric = MeanAveragePrecision(metric_target=MetricTarget.BOXES)
map_result = map_metric.update(prediction_batches, target_batches).compute()

print(map_result.map50_95)
print(map_result.map50)
print(map_result.map75)
print(map_result.matched_classes)
print(map_result.ap_per_class)
```

Use `MetricTarget.MASKS` when the question is mask overlap and both sides have
aligned masks. Use `MetricTarget.ORIENTED_BOUNDING_BOXES` when the question is
rotated-box overlap and both sides have OBB corners.

To remap classes only for mAP preparation:

```python
map_metric = MeanAveragePrecision(
    metric_target=MetricTarget.BOXES,
    class_mapping={16: 0},
)
map_result = map_metric.update(prediction_batches, target_batches).compute()
```

Use `class_agnostic=True` only when class labels should be ignored entirely.
Otherwise, wrong-class perfect overlaps should remain errors in the score.

## Compute mAR

`MeanAverageRecall` uses COCO-style top-K limits per image: @1, @10, and @100.
This is useful when many predictions compete per image.

```python
from supervision.metrics import MeanAverageRecall, MetricTarget

mar_result = (
    MeanAverageRecall(metric_target=MetricTarget.BOXES)
    .update(prediction_batches, target_batches)
    .compute()
)

print(mar_result.mAR_at_1)
print(mar_result.mAR_at_10)
print(mar_result.mAR_at_100)
print(mar_result.recall_per_class.shape)
```

If `mAR_at_1` equals `mAR_at_10` on images with many objects, verify that the
prediction confidences and image grouping are correct before interpreting the
result.

## Compute precision, recall, and F1

Use these metrics when a single aggregate detection score is easier to explain
than a full precision-recall curve.

```python
from supervision.metrics import AveragingMethod, F1Score, Precision, Recall

precision = Precision(averaging_method=AveragingMethod.WEIGHTED)
recall = Recall(averaging_method=AveragingMethod.WEIGHTED)
f1 = F1Score(averaging_method=AveragingMethod.WEIGHTED)

precision_result = precision.update(prediction_batches, target_batches).compute()
recall_result = recall.update(prediction_batches, target_batches).compute()
f1_result = f1.update(prediction_batches, target_batches).compute()

print(precision_result.precision_at_50, precision_result.precision_at_75)
print(recall_result.recall_at_50, recall_result.recall_at_75)
print(f1_result.f1_50, f1_result.f1_75)
```

Choose averaging deliberately:

```python
macro_f1 = F1Score(averaging_method=AveragingMethod.MACRO)
micro_f1 = F1Score(averaging_method=AveragingMethod.MICRO)
weighted_f1 = F1Score(averaging_method=AveragingMethod.WEIGHTED)
```

Use `MACRO` to give rare classes equal voice, `MICRO` to reflect total event
counts, and `WEIGHTED` to weight classes by target support. When a class appears
only in predictions, `MACRO` and `MICRO` can be penalized while `WEIGHTED` gives
that class zero weight by design.

## Reset and incrementally update

Metrics store internal lists until `reset()` is called:

```python
metric = F1Score()

for chunk_predictions, chunk_targets in validation_chunks:
    metric.update(chunk_predictions, chunk_targets)

result = metric.compute()
metric.reset()
```

Use one metric instance per independent evaluation. Do not reuse a metric across
model checkpoints unless you call `reset()`.

## Evaluate masks

```python
from supervision.metrics import F1Score, MeanAveragePrecision, MetricTarget

mask_map = (
    MeanAveragePrecision(metric_target=MetricTarget.MASKS)
    .update(mask_prediction_batches, mask_target_batches)
    .compute()
)
mask_f1 = (
    F1Score(metric_target=MetricTarget.MASKS)
    .update(mask_prediction_batches, mask_target_batches)
    .compute()
)
```

Before computing, assert masks exist and align with detections:

```python
for detections in [*mask_prediction_batches, *mask_target_batches]:
    if len(detections) and detections.mask is None:
        raise ValueError("MetricTarget.MASKS requires detections.mask")
```

For mask mAP, COCO-style crowd targets use `detections.data["iscrowd"]` when
present. For size buckets, mask pixel count is used unless `AREA_DATA_FIELD`
metadata overrides the area.

`ConfusionMatrix` does not support `MetricTarget.MASKS`; use box or OBB
confusion matrices, or build custom mask error visualizations after computing
mask metrics.

## Evaluate oriented bounding boxes

OBB metrics require corner coordinates in `Detections.data`:

```python
import numpy as np
from supervision.config import ORIENTED_BOX_COORDINATES
from supervision.metrics import MeanAveragePrecision, MetricTarget

obb_predictions.data[ORIENTED_BOX_COORDINATES] = np.asarray(
    prediction_corners,
    dtype=np.float32,
)  # shape: (N, 4, 2)
obb_targets.data[ORIENTED_BOX_COORDINATES] = np.asarray(
    target_corners,
    dtype=np.float32,
)

obb_result = (
    MeanAveragePrecision(metric_target=MetricTarget.ORIENTED_BOUNDING_BOXES)
    .update([obb_predictions], [obb_targets])
    .compute()
)
```

`xyxy` is still required by the `Detections` container and for some summaries,
but OBB IoU comes from `ORIENTED_BOX_COORDINATES`. If the corners come from a
model adapter, let [detection-and-zones](../../detection-and-zones/SKILL.md)
validate the adapter output.

## Build a confusion matrix from Detections

```python
import supervision as sv
from supervision.metrics import MetricTarget

cm = sv.ConfusionMatrix.from_detections(
    predictions=prediction_batches,
    targets=target_batches,
    classes=dataset.classes,
    conf_threshold=0.30,
    iou_threshold=0.50,
    metric_target=MetricTarget.BOXES,
)

print(cm.matrix)
```

The matrix has an extra row and column. The last row counts false positives by
predicted class; the last column counts false negatives by target class.

For OBB confusion matrices, use `MetricTarget.ORIENTED_BOUNDING_BOXES`. For mask
confusion matrices, choose a different metric because `ConfusionMatrix` rejects
`MetricTarget.MASKS`.

## Benchmark with a DetectionDataset and callback

Let [datasets](../../datasets/SKILL.md) load the dataset and
[detection-and-zones](../../detection-and-zones/SKILL.md) own model adapter
normalization. This sub-skill owns the metric loop:

```python
import numpy as np
import supervision as sv

# dataset = sv.DetectionDataset.from_yolo(...)
# model setup belongs outside this metrics workflow.

def callback(image: np.ndarray) -> sv.Detections:
    raw_result = run_model(image)
    return convert_result_to_detections(raw_result)

cm = sv.ConfusionMatrix.benchmark(
    dataset=dataset,
    callback=callback,
    conf_threshold=0.30,
    iou_threshold=0.50,
)
```

To save per-image validation grids:

```python
cm = sv.ConfusionMatrix.benchmark(
    dataset=dataset,
    callback=callback,
    save_directory_path="evaluation-grids",
)
```

This writes four-panel grids for each dataset image: ground truth, true
positives, false positives, and false negatives. Existing filenames in the
output directory can be overwritten with a warning. If the user needs custom
styling or additional overlays, route the visualization portion to
[annotators](../../annotators/SKILL.md) and low-level file handling to
[media-utils](../../media-utils/SKILL.md).

## Manual dataset loop for multiple metrics

A manual loop lets you compute many metrics from one prediction pass:

```python
from supervision.metrics import F1Score, MeanAveragePrecision, MeanAverageRecall

prediction_batches: list[sv.Detections] = []
target_batches: list[sv.Detections] = []

for image_path, image, targets in dataset:
    predictions = callback(image)
    prediction_batches.append(predictions)
    target_batches.append(targets)

map_result = MeanAveragePrecision().update(prediction_batches, target_batches).compute()
mar_result = MeanAverageRecall().update(prediction_batches, target_batches).compute()
f1_result = F1Score().update(prediction_batches, target_batches).compute()
```

Use this pattern when model inference is expensive and metrics should share the
same predictions.

## Remap and filter classes before scoring

If the model and dataset use different class ids, remap predictions before
metrics. For metrics other than `MeanAveragePrecision.class_mapping`, update the
`Detections` objects directly and preserve aligned data arrays by selecting the
whole container.

```python
import numpy as np

def remap_prediction_classes(
    detections: sv.Detections,
    class_id_mapping: dict[int, int],
    valid_class_ids: set[int],
) -> sv.Detections:
    if detections.class_id is None:
        raise ValueError("Predictions need class_id before metric evaluation")

    remapped = detections.copy()
    remapped.class_id = np.array(
        [class_id_mapping.get(int(class_id), int(class_id)) for class_id in remapped.class_id],
        dtype=np.int32,
    )
    keep = np.isin(remapped.class_id, list(valid_class_ids))
    return remapped[keep]
```

For `ConfusionMatrix`, make sure every final class id falls in
`[0, len(classes) - 1]`.

## Export tabular summaries

```python
map_df = map_result.to_pandas()
mar_df = mar_result.to_pandas()
f1_df = f1_result.to_pandas()
```

`.to_pandas()` gives summary columns such as `mAP@50:95`, `P@50`, or `F1@50` and
size-bucket columns. Keep `matched_classes` plus per-class arrays if the user
needs a full per-class report.

For a custom per-class table:

```python
rows = []
for class_id, scores in zip(f1_result.matched_classes, f1_result.f1_per_class):
    rows.append({"class_id": int(class_id), "f1_50": float(scores[0])})
```

## Plot optional summaries

```python
map_result.plot()
f1_result.plot()
fig = cm.plot(title="Validation confusion matrix", normalize=True)
```

For non-interactive environments, prefer `ConfusionMatrix.plot(save_path="cm.png")`
or collect numeric results instead of relying on a display. The new metric result
`.plot()` methods show summary charts and do not save directly; use the returned
numeric fields for durable reports, or build a custom figure in the application.
