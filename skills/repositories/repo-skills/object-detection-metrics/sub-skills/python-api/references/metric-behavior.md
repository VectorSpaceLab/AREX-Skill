# Metric behavior and edge cases

This repository implements legacy PASCAL VOC-style object-detection metrics. The behavior below is important when using the API directly.

## Class and image matching

`Evaluator.GetPascalVOCMetrics` separates boxes into ground truths and detections, then evaluates each class independently:

1. Classes are collected from both ground truths and detections and sorted.
2. Ground truths are grouped by `imageName` for each class.
3. Detections for the class are sorted by descending `classConfidence`.
4. Each detection is compared only with ground truths that have the same class and the same `imageName`.
5. A detection with IoU greater than or equal to `IOUThreshold` can match an unmatched ground truth and become TP.
6. If the best matching ground truth for that image was already matched, the detection is FP.
7. If no same-image ground truth has sufficient IoU, the detection is FP.

Implications:

- Keep `imageName` stable across GT and detection objects. Do not mix `000001` and `000001.jpg` unless both sides use the same string.
- Always pass numeric confidences for detections. They control evaluation order.
- Classes that appear only in detections have zero positives and can trigger divide-by-zero / NaN behavior. For robust evaluation, provide ground truths for each evaluated class or filter unsupported detections first.

## Duplicate detections

For one ground truth and multiple overlapping detections:

- The highest-confidence detection is processed first.
- If it meets the IoU threshold, it is TP and marks the ground truth as used.
- Later detections overlapping the same used ground truth are FP.

This means a perfect high-confidence detection followed by a duplicate lower-confidence detection can still report AP `1.0` while reporting `total TP = 1` and `total FP = 1`. Inspect TP/FP totals, not just AP.

## IoU uses inclusive pixel-area arithmetic

The source implementation treats `(x1, y1, x2, y2)` boxes as inclusive pixel coordinates:

- Area is `(x2 - x1 + 1) * (y2 - y1 + 1)`.
- Intersection area also uses `+ 1` on width and height.
- Boxes that touch at a boundary can have a nonzero intersection under this convention.

For example, `Evaluator.iou((0, 0, 10, 10), (10, 0, 20, 10))` is nonzero because the shared `x=10` column is counted. If your upstream data uses half-open boxes or continuous geometry, convert or document the convention before comparing to other metric libraries.

## AP method selection

Use the enum value, not a string, when calling the API:

```python
method = MethodAveragePrecision.EveryPointInterpolation
# or
method = MethodAveragePrecision.ElevenPointInterpolation
```

`EveryPointInterpolation` calls `Evaluator.CalculateAveragePrecision(rec, prec)`:

- Pads recall with `0` and `1`.
- Pads precision with leading and trailing `0`.
- Builds a monotonically non-increasing precision envelope from right to left.
- Integrates precision at recall changes.

`ElevenPointInterpolation` calls `Evaluator.ElevenPointInterpolatedAP(rec, prec)`:

- Uses recall thresholds `0.0, 0.1, ..., 1.0`.
- At each threshold, uses the maximum precision observed at any recall greater than or equal to that threshold.
- Averages the eleven precision values.

Both methods return an AP scalar plus interpolation arrays; the arrays are intended for plotting and may not have the same shape or ordering across methods.

## mAP calculation

`GetPascalVOCMetrics` returns per-class dictionaries only. To compute mAP, average the per-class `AP` values yourself:

```python
metrics = Evaluator().GetPascalVOCMetrics(boxes, IOUThreshold=0.5, method=method)
map_value = sum(float(m["AP"]) for m in metrics) / len(metrics) if metrics else 0.0
```

When comparing with the repository CLI, confirm the same IoU threshold, coordinate format, relative coordinate conversion, and AP interpolation method.

## Coordinate conversion behavior

Relative coordinates are normalized center coordinates:

```text
x = center_x / image_width
y = center_y / image_height
w = box_width / image_width
h = box_height / image_height
```

`convertToAbsoluteValues((width, height), (x, y, w, h))`:

- rounds computed endpoints,
- clamps negative top-left values to `0`,
- clamps right/bottom endpoints to `width - 1` and `height - 1`,
- returns `(x1, y1, x2, y2)`.

A `BoundingBox` constructed with relative coordinates stores converted absolute values and can return both `XYWH` and `XYX2Y2` formats.

## Plotting and drawing semantics

- `PlotPrecisionRecallCurve` first calls `GetPascalVOCMetrics`, then uses matplotlib. It defaults to `showGraphic=True`; set `showGraphic=False` for noninteractive execution.
- If `savePath` is supplied, one PNG per class is written below that directory. The directory must already exist.
- `BoundingBoxes.drawAllBoundingBoxes(image, imageName)` draws into an OpenCV image array for the selected `imageName`; it returns the modified image and does not save it.
