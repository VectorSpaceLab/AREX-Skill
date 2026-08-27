---
name: metrics
description: "Use supervision metrics for detection evaluation, benchmarking,
  and result interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Metrics

Use this sub-skill when a task asks to evaluate object detection, instance
segmentation, or oriented-box predictions with `supervision` metrics in version
`0.31.0.dev0` on Python `>=3.10`.

## Route here for

- `MeanAveragePrecision`, `MeanAverageRecall`, `Precision`, `Recall`,
  `F1Score`, result objects, `.update(...)`, `.compute()`, `.reset()`,
  `.to_pandas()`, or `.plot()`.
- `MetricTarget.BOXES`, `MetricTarget.MASKS`,
  `MetricTarget.ORIENTED_BOUNDING_BOXES`, and `AveragingMethod` choices.
- `sv.ConfusionMatrix`, confusion-matrix plots, confidence/IoU thresholds, and
  per-image validation grids from `ConfusionMatrix.benchmark(...)`.
- Dataset-backed benchmark loops that already have or can obtain pairs of
  prediction and target `Detections`.
- Diagnosing mAP, mAR, precision, recall, F1, per-class rows, weighted versus
  macro/micro averaging, empty inputs, class-id mapping, masks, OBB metrics,
  COCO-style `area`, `iscrowd`, and `ignore` behavior.

## Route away

- Dataset loading, splitting, merging, or format conversion: use
  [datasets](../datasets/SKILL.md), then return here with `DetectionDataset`
  samples or `Detections` target lists.
- Model inference, framework adapters, VLM parsing, detection filtering, NMS,
  masks/OBB container construction, zones, slicers, or sinks: use
  [detection-and-zones](../detection-and-zones/SKILL.md), then return here with
  prediction `Detections`.
- High-level false-positive/false-negative drawing or side-by-side visual style:
  use [annotators](../annotators/SKILL.md) after metrics identify the detections
  to display.
- Low-level image/video I/O, plotting grids, or OpenCV backend diagnosis: use
  [media-utils](../media-utils/SKILL.md) when the task is not metric-specific.

## Start with these references

- [Metrics reference](references/metrics-reference.md) for metric classes,
  required `Detections` fields, result attributes, targets, averaging, and
  COCO-style metadata.
- [Workflows](references/workflows.md) for update/compute patterns,
  dataset-backed benchmark loops, class remapping, mask/OBB evaluation,
  confusion matrices, pandas export, and plotting.
- [Troubleshooting](references/troubleshooting.md) for metrics extra/pandas,
  missing `confidence` or `class_id`, wrong `MetricTarget`, mask/OBB metadata,
  class mappings, empty inputs, and visualization issues.

## Operating defaults

1. Install the metrics extra before metric work: `pip install "supervision[metrics]"`.
   The base install is `pip install supervision`, but `.to_pandas()` needs pandas
   from the metrics extra.
2. Prefer the newer metrics package imports:
   `from supervision.metrics import MeanAveragePrecision, MeanAverageRecall,
   Precision, Recall, F1Score, MetricTarget, AveragingMethod`. Do not use the
   legacy top-level `sv.MeanAveragePrecision` for new mAP code.
3. Predictions must normally include `xyxy`, `class_id`, and `confidence`.
   Targets must include `xyxy` and `class_id`; target `confidence` is not
   required.
4. Choose the metric target deliberately. `BOXES` uses `detections.xyxy`,
   `MASKS` uses `detections.mask`, and `ORIENTED_BOUNDING_BOXES` uses
   `detections.data[ORIENTED_BOX_COORDINATES]`.
5. Keep class ids aligned with the dataset class list before computing metrics.
   `ConfusionMatrix` requires ids in `[0, len(classes) - 1]`; new metric result
   rows are keyed by `matched_classes` rather than by row position alone.
6. Do not promise network/model benchmark execution unless the user already
   provides a runnable model and local dataset. This skill owns evaluation logic,
   not model acquisition or data download.
