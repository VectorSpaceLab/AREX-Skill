# Evaluation Data Formats and Metric Math

## Folder layout

Evaluation consumes two required folders and one optional folder:

```text
ground-truth/
  image_1.txt
  image_2.txt
detection-results/
  image_1.txt
  image_2.txt
images-optional/
  image_1.jpg
  image_2.jpg
```

Rules:

- `ground-truth/` and `detection-results/` must contain one `.txt` file per evaluated image.
- Files match by basename: `image_1.txt` in ground truth must have `image_1.txt` in detection results, and vice versa.
- Image files are only needed for optional animation/annotated-frame output. Their basenames must match the `.txt` ids.
- Use pixel-coordinate boxes in `left top right bottom` order. The evaluator uses the inclusive VOC convention, so width and height are computed with `+1`.

## Ground-truth rows

Each non-empty row in a ground-truth file is:

```text
<class_name> <left> <top> <right> <bottom> [difficult]
```

Example:

```text
tvmonitor 2 10 173 238
book 439 157 556 241
book 437 246 518 351 difficult
pottedplant 272 190 316 259
```

Notes:

- `class_name` is a single token. Replace spaces in class names before evaluation.
- `difficult` is optional and must be the exact last token when present.
- Difficult ground-truth boxes do not increase the class's positive-object count. A detection matched to a difficult box is ignored rather than counted as TP or FP.
- A class removed with `--ignore` is skipped before class counts and metric denominators are built.

## Detection-result rows

Each non-empty row in a detection-results file is:

```text
<class_name> <confidence> <left> <top> <right> <bottom>
```

Example:

```text
tvmonitor 0.471781 0 13 174 244
cup 0.414941 274 226 301 265
book 0.460851 429 219 528 247
chair 0.292345 0 199 88 436
```

Notes:

- `confidence` must be numeric. Detections are sorted by decreasing confidence per class before matching.
- Coordinates may be integer or floating point values, but `left <= right` and `top <= bottom` must hold.
- Detections for classes not present in non-ignored, non-difficult ground truth are not AP classes. They still appear in detected-object summaries with zero true positives.
- Detections for ignored classes are omitted from matching and detected-object summaries.

## IoU and detection assignment

For each class:

1. Sort detections of that class by decreasing confidence.
2. For each detection, find the same-class ground-truth box in the same image with the largest IoU.
3. Use the default IoU threshold `0.5` unless a per-class threshold was supplied.
4. Count the detection as:
   - **TP** if IoU is at least the threshold, the matched GT box is not difficult, and that GT box was not already used.
   - **FP** if no same-class match exists, IoU is below threshold, or the matched non-difficult GT box was already used by a higher-confidence detection.
   - **ignored** if it matches a difficult GT box at or above threshold.

IoU uses the PASCAL VOC inclusive-pixel formula:

```text
intersection_width  = min(det_right, gt_right) - max(det_left, gt_left) + 1
intersection_height = min(det_bottom, gt_bottom) - max(det_top, gt_top) + 1
IoU = intersection_area / (det_area + gt_area - intersection_area)
```

If either intersection dimension is not positive, IoU is `0`.

## AP and mAP

For each class with at least one non-ignored, non-difficult ground-truth object:

1. Build cumulative TP and FP arrays in detection confidence order.
2. Compute recall as `TP / number_of_ground_truth_objects_for_class`.
3. Compute precision as `TP / (TP + FP)`.
4. Convert precision to the VOC monotonic precision envelope by replacing each precision value with the maximum precision to its right.
5. AP is the exact area under that piecewise-constant precision/recall curve.

mAP is the arithmetic mean of AP values over evaluated classes. Ignored classes and classes that only appear as difficult ground truth do not contribute to the denominator.

## Per-class IoU overrides

Use class-specific thresholds when the benchmark requires a threshold other than the global default:

```bash
python scripts/run_map_evaluation.py ... --set-class-iou person 0.7 car 0.6
```

Validation rules:

- Arguments must be `CLASS IOU` pairs.
- Each class must remain in the evaluated ground-truth class set after `--ignore` is applied.
- IoU values must be numeric and strictly between `0.0` and `1.0`.
- Do not provide the same class twice in one command.
